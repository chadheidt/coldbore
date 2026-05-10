// Cold Bore download proxy.
// Validates beta access codes and serves files from R2 via short-lived signed URLs.
//
// **THIS IS A BACKUP COPY.** The live source-of-truth is the deployed version in
// the Cloudflare dashboard at:
//     dash.cloudflare.com -> Workers & Pages -> coldbore-download -> Edit code
//
// To redeploy: paste this file's contents into the dashboard editor, click Deploy.
// To version-control properly later, install wrangler (`npm install -g wrangler`),
// `wrangler login`, then `wrangler deploy` from this folder.
//
// Endpoints:
//   POST /authorize  body: {code, file}  -> returns {url} (5-min signed URL)
//   GET  /get/<file>?exp=&sig=           -> serves the file
//
// Bindings expected (configured in dashboard, NOT in this file):
//   BUCKET       -> R2 bucket "coldbore-releases"
//   HMAC_SECRET  -> encrypted env var (long random string)

const VALID_CODES = new Set([
  "CBORE-DDCX-AEGK-J2FR-2SIB",
  "CBORE-4O4I-YXZR-3VZL-XE74",
  "CBORE-ZLXI-SZH2-63DK-KZPX",
  "CBORE-LHNF-IMIT-IISA-IXFS",
  "CBORE-T7XV-Y7M7-L54X-FOHP",
  "CBORE-ROQG-NCQR-CAXN-N53D",
]);

const ALLOWED_FILES = new Set(["Cold.Bore.dmg", "Cold.Bore.zip"]);

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400",
};

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

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: CORS });
    }

    // POST /authorize : validate code, return signed download URL
    if (url.pathname === "/authorize" && request.method === "POST") {
      let body;
      try { body = await request.json(); }
      catch { return jsonResponse({ error: "Bad request" }, 400); }

      const code = normalizeCode(body.code);
      const file = body.file || "Cold.Bore.dmg";

      if (!VALID_CODES.has(code)) {
        return jsonResponse({ error: "Code not recognized. Please contact coldboreapp@gmail.com." }, 403);
      }
      if (!ALLOWED_FILES.has(file)) {
        return jsonResponse({ error: "Invalid file" }, 400);
      }

      const expiry = Math.floor(Date.now() / 1000) + 300; // 5 min
      const payload = `${file}|${expiry}`;
      const sig = await hmacSha256Hex(payload, env.HMAC_SECRET);
      const downloadUrl = `${url.origin}/get/${encodeURIComponent(file)}?exp=${expiry}&sig=${sig}`;

      return jsonResponse({ url: downloadUrl });
    }

    // GET /get/<file>?exp=&sig=  : verify signature, stream file from R2
    if (url.pathname.startsWith("/get/") && request.method === "GET") {
      const file = decodeURIComponent(url.pathname.slice("/get/".length));
      const expiry = parseInt(url.searchParams.get("exp") || "0", 10);
      const sig = url.searchParams.get("sig") || "";

      if (!ALLOWED_FILES.has(file)) {
        return new Response("Not found", { status: 404, headers: CORS });
      }
      if (!expiry || Math.floor(Date.now() / 1000) > expiry) {
        return new Response("Link expired — please re-enter your code.", { status: 403, headers: CORS });
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

    return new Response("Not found", { status: 404, headers: CORS });
  }
};
