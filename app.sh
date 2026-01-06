#!/usr/bin/env bash
echo "=== APP.SH MARKER: I AM RUNNING ==="
exit 0

set -e
 
cd /repos/LoE-Assistant/loe-frontend
 
echo "PWD=$(pwd)"
echo "PORT=$PORT"
echo "Listing loe-frontend:"
ls -la
 
echo "vite.config.js contents (if present):"
ls -la vite.config.* || true
cat vite.config.js || true
 
 
# Always do a clean install in the App container
rm -rf node_modules
 
# npm sometimes skips optional deps; this helps
npm install --include=optional
 
# Build using node directly (avoids vite permission issues)
node node_modules/vite/bin/vite.js build
 
# Serve the built app
npx --yes serve dist --single --listen tcp://0.0.0.0:${PORT}