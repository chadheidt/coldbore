// Loadscope download proxy + beta-access automation.
//
// **THIS IS A BACKUP COPY.** The live source-of-truth is the deployed version in
// the Cloudflare dashboard at:
//     dash.cloudflare.com -> Workers & Pages -> coldbore-download -> Edit code
//
// (Worker kept under the legacy "coldbore-download" name so existing v0.11.x
// users -- whose app has the URL baked in -- can still auto-update past v0.11.3.
// Rename in a future commercial-launch session if desired.)
//
// To redeploy: paste this file's contents into the dashboard editor, click Deploy.
// To version-control properly later, install wrangler (`npm install -g wrangler`),
// `wrangler login`, then `wrangler deploy` from this folder.
//
// Endpoints:
//   POST /authorize              body: {code, file}  -> {url} (5-min signed URL)   [existing]
//   GET  /get/<file>?exp=&sig=                       -> serves the file            [existing]
//   POST /request-access         body: {name,email,project_info,turnstile_token}
//                                                     -> stores request, emails admin
//   GET  /approve?id=&token=                         -> picks next key, emails tester
//   GET  /deny?id=&token=                            -> marks request denied
//   GET  /admin/assignments?token=<ADMIN_TOKEN>      -> JSON dump of all assignments
//                                                       (used by tools/sync_beta_keys.py)
//
// Bindings expected (configured in dashboard, NOT in this file):
//   BUCKET            -> R2 bucket "coldbore-releases"
//   HMAC_SECRET       -> encrypted env var (long random string)
//   BETA_REQUESTS     -> KV namespace (stores request + assignment state)
//   RESEND_API_KEY    -> encrypted env var (re_xxx from resend.com)
//   FROM_EMAIL        -> e.g. "Loadscope <noreply@loadscope.app>"
//   ADMIN_EMAIL       -> Chad's gmail (where approve/deny links land)
//   ADMIN_TOKEN       -> encrypted env var (random string for /admin/* auth)
//   TURNSTILE_SECRET  -> encrypted env var (anti-bot)
//   PUBLIC_SITE       -> e.g. "https://chadheidt.github.io/coldbore/"

const VALID_CODES = new Set([
  "CBORE-DDCX-AEGK-J2FR-2SIB",
  "CBORE-4O4I-YXZR-3VZL-XE74",
  "CBORE-ZLXI-SZH2-63DK-KZPX",
  "CBORE-LHNF-IMIT-IISA-IXFS",
  "CBORE-T7XV-Y7M7-L54X-FOHP",
  "CBORE-ROQG-NCQR-CAXN-N53D",
  "CBORE-KZYC-TJRE-DAFV-LCOY",
  "CBORE-H453-IKCN-2YHY-CPJR",
  "CBORE-3LMH-IXAV-JXWT-URJ5",
  "CBORE-AADE-RUVG-VLJU-PAWQ",
  "CBORE-L5CI-RHZE-FGWP-WXL2",
]);

const ALLOWED_FILES = new Set(["Loadscope.dmg", "Loadscope.zip", "Cold.Bore.dmg", "Cold.Bore.zip"]);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400",
};

// ---------- Utilities ----------

function normalizeCode(s) {
  if (!s) return "";
  return String(s).trim().toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-|-$/g, "");
}

async function hmacSha256Hex(message, secret) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(message));
  return [...new Uint8Array(sig)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}

function htmlResponse(html, status = 200) {
  return new Response(html, {
    status,
    headers: { ...CORS, "Content-Type": "text/html; charset=utf-8" },
  });
}

// Generate a short, URL-safe random id.
function randomId(bytes = 16) {
  const buf = new Uint8Array(bytes);
  crypto.getRandomValues(buf);
  return [...buf].map(b => b.toString(16).padStart(2, "0")).join("");
}

function escapeHtml(s) {
  if (s === null || s === undefined) return "";
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function isEmail(s) {
  return typeof s === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s) && s.length < 200;
}

// ---------- Email (Resend) ----------

async function sendEmail(env, { to, subject, html, replyTo }) {
  const body = {
    from: env.FROM_EMAIL,
    to: [to],
    subject,
    html,
  };
  if (replyTo) body.reply_to = replyTo;

  const resp = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`Resend send failed (${resp.status}): ${text}`);
  }
  return await resp.json();
}

// ---------- Turnstile validation ----------

async function validateTurnstile(env, token, ip) {
  if (!token) return false;
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET);
  form.append("response", token);
  if (ip) form.append("remoteip", ip);

  const resp = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: form,
  });
  if (!resp.ok) return false;
  const result = await resp.json();
  return result.success === true;
}

// ---------- KV helpers ----------

const REQUEST_TTL_SECONDS = 60 * 60 * 24 * 30; // requests expire from KV after 30 days
const ASSIGNMENT_TTL_SECONDS = 60 * 60 * 24 * 365 * 2; // assignments kept 2 years

// Codes that are part of VALID_CODES (so they unlock the website's "I have a code"
// download flow) but should NEVER be auto-handed out by the request-access flow.
// Chad's local-testing key lives here. Anything in this set is also recorded as
// permanently "assigned" in KV (see the bootstrap doc) so an empty-KV recovery
// wouldn't accidentally start handing it to testers.
const RESERVED_CODES = new Set([
  "CBORE-DDCX-AEGK-J2FR-2SIB", // Chad Heidt — local testing
]);

async function pickNextUnassignedKey(env) {
  for (const code of VALID_CODES) {
    if (RESERVED_CODES.has(code)) continue;
    const existing = await env.BETA_REQUESTS.get(`assigned:${code}`);
    if (!existing) {
      return code;
    }
  }
  return null;
}

async function recordAssignment(env, code, requestData) {
  const payload = {
    name: requestData.name,
    email: requestData.email,
    project_info: requestData.project_info || "",
    request_id: requestData.request_id,
    assigned_at: new Date().toISOString(),
  };
  await env.BETA_REQUESTS.put(`assigned:${code}`, JSON.stringify(payload), {
    expirationTtl: ASSIGNMENT_TTL_SECONDS,
  });
}

// ---------- Email templates ----------

function adminNotificationEmail(env, baseUrl, request) {
  const approveUrl = `${baseUrl}/approve?id=${encodeURIComponent(request.id)}&token=${encodeURIComponent(request.token)}`;
  const denyUrl = `${baseUrl}/deny?id=${encodeURIComponent(request.id)}&token=${encodeURIComponent(request.token)}`;
  const html = `
    <div style="font-family: -apple-system, sans-serif; max-width: 560px; margin: 0 auto; color: #111;">
      <h2 style="margin: 0 0 16px;">Loadscope beta access request</h2>
      <table style="border-collapse: collapse; width: 100%; margin-bottom: 20px;">
        <tr><td style="padding: 6px 0; color: #555; width: 110px;">Name</td><td style="padding: 6px 0;"><strong>${escapeHtml(request.name)}</strong></td></tr>
        <tr><td style="padding: 6px 0; color: #555;">Email</td><td style="padding: 6px 0;">${escapeHtml(request.email)}</td></tr>
        ${request.project_info ? `<tr><td style="padding: 6px 0; color: #555; vertical-align: top;">Notes</td><td style="padding: 6px 0;">${escapeHtml(request.project_info)}</td></tr>` : ""}
        <tr><td style="padding: 6px 0; color: #555;">IP</td><td style="padding: 6px 0; color: #888;">${escapeHtml(request.ip || "")}</td></tr>
        <tr><td style="padding: 6px 0; color: #555;">Submitted</td><td style="padding: 6px 0; color: #888;">${escapeHtml(request.timestamp)}</td></tr>
      </table>
      <div style="margin-top: 24px;">
        <a href="${approveUrl}" style="background: #16a34a; color: #fff; text-decoration: none; padding: 12px 22px; border-radius: 6px; display: inline-block; margin-right: 8px;">Approve</a>
        <a href="${denyUrl}" style="background: #dc2626; color: #fff; text-decoration: none; padding: 12px 22px; border-radius: 6px; display: inline-block;">Deny</a>
      </div>
      <p style="color: #666; font-size: 13px; margin-top: 24px;">
        Approving picks the next unassigned slot from the 10 pre-generated beta keys, records the assignment, and emails the tester their code.
        Once you click either button it cannot be re-clicked -- the link becomes one-shot.
      </p>
    </div>
  `;
  return {
    to: env.ADMIN_EMAIL,
    subject: `Beta access request from ${request.name}`,
    html,
    replyTo: request.email,
  };
}

function testerWelcomeEmail(env, request, code) {
  const html = `
    <div style="font-family: -apple-system, sans-serif; max-width: 560px; margin: 0 auto; color: #111;">
      <h2 style="margin: 0 0 16px;">Welcome to Loadscope</h2>
      <p>Hi ${escapeHtml(request.name.split(/\s+/)[0])},</p>
      <p>You're in. Your beta access code:</p>
      <p style="background: #f3f4f6; border: 1px solid #d1d5db; padding: 14px 18px; border-radius: 6px; font-family: Menlo, Consolas, monospace; font-size: 16px; letter-spacing: 0.5px; margin: 20px 0;">
        <strong>${escapeHtml(code)}</strong>
      </p>
      <p>What to do with it:</p>
      <ol>
        <li>Visit <a href="${escapeHtml(env.PUBLIC_SITE)}" style="color: #d97706;">${escapeHtml(env.PUBLIC_SITE)}</a></li>
        <li>Click <strong>Download</strong>.</li>
        <li>Paste the code above when prompted -- the .dmg downloads.</li>
        <li>Open the .dmg, drag <strong>Loadscope</strong> to your Applications folder.</li>
        <li>Launch Loadscope. Paste the same code into the license dialog on first run.</li>
      </ol>
      <p>You'll get auto-updates in-app from now on -- no need to re-download from the website.</p>
      <p style="color: #555; font-size: 14px; margin-top: 28px;">
        Please don't share the code -- each tester has a unique one so we can follow up individually. If something breaks, hit reply on this email.
      </p>
      <p style="color: #888; font-size: 13px; margin-top: 18px;">-- Chad</p>
    </div>
  `;
  return {
    to: request.email,
    subject: "Your Loadscope beta access code",
    html,
    replyTo: env.ADMIN_EMAIL,
  };
}

// ---------- Handlers ----------

async function handleRequestAccess(request, env, url) {
  let body;
  try { body = await request.json(); }
  catch { return jsonResponse({ error: "Bad request" }, 400); }

  const name = String(body.name || "").trim();
  const email = String(body.email || "").trim().toLowerCase();
  const projectInfo = String(body.project_info || "").trim().slice(0, 1000);
  const turnstileToken = String(body.turnstile_token || "");

  // Basic validation
  if (name.length < 2 || name.length > 120) {
    return jsonResponse({ error: "Please enter your name." }, 400);
  }
  if (!isEmail(email)) {
    return jsonResponse({ error: "Please enter a valid email." }, 400);
  }

  // Turnstile anti-bot
  const ip = request.headers.get("CF-Connecting-IP") || "";
  const turnstileOk = await validateTurnstile(env, turnstileToken, ip);
  if (!turnstileOk) {
    return jsonResponse({ error: "Anti-bot check failed. Please reload the page and try again." }, 403);
  }

  // Soft rate limit: one request per IP per 24h
  if (ip) {
    const ipKey = `ratelimit:ip:${ip}`;
    const recent = await env.BETA_REQUESTS.get(ipKey);
    if (recent) {
      return jsonResponse({ error: "We already have a recent request from this network. If you didn't send it, please try again tomorrow." }, 429);
    }
    await env.BETA_REQUESTS.put(ipKey, "1", { expirationTtl: 60 * 60 * 24 });
  }

  // Build the request record
  const id = randomId(16);
  const token = randomId(32);
  const record = {
    id,
    token,
    name,
    email,
    project_info: projectInfo,
    ip,
    timestamp: new Date().toISOString(),
    status: "pending",
  };

  await env.BETA_REQUESTS.put(`req:${id}`, JSON.stringify(record), {
    expirationTtl: REQUEST_TTL_SECONDS,
  });

  // Email Chad with approve/deny links
  try {
    const baseUrl = url.origin;
    await sendEmail(env, adminNotificationEmail(env, baseUrl, record));
  } catch (err) {
    // Don't fail the user's submission if the email fails -- the record is in KV.
    // Chad can pull it up via a future admin endpoint. For now just log.
    console.error("admin notification email failed:", err.message);
  }

  return jsonResponse({
    ok: true,
    message: "Thanks. Your request is in the queue -- you'll get an email with your access code once it's approved (usually within 24 hours).",
  });
}

async function handleApprove(request, env, url) {
  const id = url.searchParams.get("id");
  const token = url.searchParams.get("token");
  if (!id || !token) {
    return htmlResponse("<h2>Invalid link</h2><p>Missing parameters.</p>", 400);
  }

  const raw = await env.BETA_REQUESTS.get(`req:${id}`);
  if (!raw) {
    return htmlResponse("<h2>Request not found</h2><p>This request may have expired or been processed already.</p>", 404);
  }

  const record = JSON.parse(raw);
  if (record.token !== token) {
    return htmlResponse("<h2>Invalid token</h2><p>This link is not authentic.</p>", 403);
  }
  if (record.status !== "pending") {
    return htmlResponse(`<h2>Already ${escapeHtml(record.status)}</h2><p>This request was already handled. Code: <code>${escapeHtml(record.assigned_code || "(none)")}</code></p>`, 200);
  }

  // Pick next unassigned slot
  const code = await pickNextUnassignedKey(env);
  if (!code) {
    return htmlResponse("<h2>No keys available</h2><p>All 10 beta slots are assigned. Generate more in app/license.py and the Worker, then re-deploy before approving more.</p>", 500);
  }

  // Record assignment
  await recordAssignment(env, code, { ...record, request_id: id });

  // Update request to "approved"
  record.status = "approved";
  record.assigned_code = code;
  record.approved_at = new Date().toISOString();
  await env.BETA_REQUESTS.put(`req:${id}`, JSON.stringify(record), {
    expirationTtl: REQUEST_TTL_SECONDS,
  });

  // Email tester
  let emailOk = true;
  let emailError = "";
  try {
    await sendEmail(env, testerWelcomeEmail(env, record, code));
  } catch (err) {
    emailOk = false;
    emailError = err.message || String(err);
  }

  const emailLine = emailOk
    ? `<p style="color: #16a34a;">Welcome email sent to <strong>${escapeHtml(record.email)}</strong>.</p>`
    : `<p style="color: #dc2626;">Failed to email the tester (${escapeHtml(emailError)}). Send the code to them manually.</p>`;

  return htmlResponse(`
    <html><body style="font-family: -apple-system, sans-serif; max-width: 560px; margin: 60px auto; padding: 0 20px; color: #111;">
      <h2>Approved.</h2>
      <p>Assigned code <code style="background: #f3f4f6; padding: 4px 8px; border-radius: 4px;">${escapeHtml(code)}</code> to <strong>${escapeHtml(record.name)}</strong> (${escapeHtml(record.email)}).</p>
      ${emailLine}
      <p style="color: #888; font-size: 13px; margin-top: 30px;">
        Don't forget to update beta-keys.txt locally:<br>
        <code>python3 tools/sync_beta_keys.py</code>
      </p>
    </body></html>
  `);
}

async function handleDeny(request, env, url) {
  const id = url.searchParams.get("id");
  const token = url.searchParams.get("token");
  if (!id || !token) {
    return htmlResponse("<h2>Invalid link</h2><p>Missing parameters.</p>", 400);
  }

  const raw = await env.BETA_REQUESTS.get(`req:${id}`);
  if (!raw) {
    return htmlResponse("<h2>Request not found</h2>", 404);
  }

  const record = JSON.parse(raw);
  if (record.token !== token) {
    return htmlResponse("<h2>Invalid token</h2>", 403);
  }
  if (record.status !== "pending") {
    return htmlResponse(`<h2>Already ${escapeHtml(record.status)}</h2>`, 200);
  }

  record.status = "denied";
  record.denied_at = new Date().toISOString();
  await env.BETA_REQUESTS.put(`req:${id}`, JSON.stringify(record), {
    expirationTtl: REQUEST_TTL_SECONDS,
  });

  return htmlResponse(`
    <html><body style="font-family: -apple-system, sans-serif; max-width: 560px; margin: 60px auto; padding: 0 20px; color: #111;">
      <h2>Denied.</h2>
      <p>Request from <strong>${escapeHtml(record.name)}</strong> (${escapeHtml(record.email)}) marked denied. No email sent.</p>
    </body></html>
  `);
}

// ---------- Admin endpoint (for tools/sync_beta_keys.py) ----------

async function handleAdminAssignments(request, env, url) {
  const token = url.searchParams.get("token") || "";
  if (!env.ADMIN_TOKEN || token !== env.ADMIN_TOKEN) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }

  // List all keys with the "assigned:" prefix and fetch each value.
  const assignments = [];
  let cursor = undefined;
  do {
    const page = await env.BETA_REQUESTS.list({ prefix: "assigned:", cursor });
    for (const k of page.keys) {
      const code = k.name.slice("assigned:".length);
      const raw = await env.BETA_REQUESTS.get(k.name);
      if (raw) {
        try {
          const data = JSON.parse(raw);
          assignments.push({
            code,
            name: data.name || "",
            email: data.email || "",
            assigned_at: data.assigned_at || "",
          });
        } catch {
          // skip malformed
        }
      }
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  return jsonResponse({ assignments });
}

// ---------- Existing handlers (preserved) ----------

async function handleAuthorize(request, env, url) {
  let body;
  try { body = await request.json(); }
  catch { return jsonResponse({ error: "Bad request" }, 400); }

  const code = normalizeCode(body.code);
  const file = body.file || "Loadscope.dmg";

  if (!VALID_CODES.has(code)) {
    return jsonResponse({ error: "Code not recognized. Please contact support@loadscope.app." }, 403);
  }
  if (!ALLOWED_FILES.has(file)) {
    return jsonResponse({ error: "Invalid file" }, 400);
  }

  const expiry = Math.floor(Date.now() / 1000) + 300;
  const payload = `${file}|${expiry}`;
  const sig = await hmacSha256Hex(payload, env.HMAC_SECRET);
  const downloadUrl = `${url.origin}/get/${encodeURIComponent(file)}?exp=${expiry}&sig=${sig}`;

  return jsonResponse({ url: downloadUrl });
}

async function handleGet(request, env, url) {
  const file = decodeURIComponent(url.pathname.slice("/get/".length));
  const expiry = parseInt(url.searchParams.get("exp") || "0", 10);
  const sig = url.searchParams.get("sig") || "";

  if (!ALLOWED_FILES.has(file)) {
    return new Response("Not found", { status: 404, headers: CORS });
  }
  if (!expiry || Math.floor(Date.now() / 1000) > expiry) {
    return new Response("Link expired -- please re-enter your code.", { status: 403, headers: CORS });
  }
  const expected = await hmacSha256Hex(`${file}|${expiry}`, env.HMAC_SECRET);
  if (sig !== expected) {
    return new Response("Invalid signature", { status: 403, headers: CORS });
  }

  const obj = await env.BUCKET.get(file);
  if (!obj) {
    return new Response("File not found in storage", { status: 404, headers: CORS });
  }

  const headers = new Headers();
  obj.writeHttpMetadata(headers);
  headers.set("Content-Disposition", `attachment; filename="${file}"`);
  headers.set("Content-Length", String(obj.size));
  return new Response(obj.body, { headers });
}

// ---------- Router ----------

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    if (url.pathname === "/authorize" && request.method === "POST") {
      return handleAuthorize(request, env, url);
    }
    if (url.pathname.startsWith("/get/") && request.method === "GET") {
      return handleGet(request, env, url);
    }
    if (url.pathname === "/request-access" && request.method === "POST") {
      return handleRequestAccess(request, env, url);
    }
    if (url.pathname === "/approve" && request.method === "GET") {
      return handleApprove(request, env, url);
    }
    if (url.pathname === "/deny" && request.method === "GET") {
      return handleDeny(request, env, url);
    }
    if (url.pathname === "/admin/assignments" && request.method === "GET") {
      return handleAdminAssignments(request, env, url);
    }

    return new Response("Not found", { status: 404, headers: CORS });
  }
};
