#!/bin/bash
# Generate the True Zero app icon.
# Produces app/resources/AppIcon.icns from a procedural Qt drawing.
# After this finishes, rebuild the .app via Build App.command to bake the new icon in.

set -e

PROJECT="$HOME/Projects/Rifle Load Data"
cd "$PROJECT"

echo "============================================================"
echo "Generating True Zero app icon"
echo "============================================================"
echo ""

/usr/bin/python3 app/resources/generate_icon.py

echo ""
echo "Now rebuild the .app:"
echo "    double-click  Build App.command"
echo "============================================================"
