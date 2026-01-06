#!/usr/bin/env bash
set -euxo pipefail

echo "=== APP.SH START ==="
whoami
pwd
echo "PORT=${PORT:-<empty>}"
env | grep -E 'DOMINO|KUBERNETES|PORT' || true
echo "=== APP.SH ENV DONE ==="

cd /repos/LoE-Assistant/loe-frontend

echo "=== LOCATION CHECK ==="
pwd
ls -la
echo "======================"

echo "=== vite.config.js (if present) ==="
ls -la vite.config.* || true
cat vite.config.js || true
echo "=================================="

echo "=== CLEAN INSTALL ==="
rm -rf node_modules
npm install --include=optional

echo "=== BUILD WITH VITE ==="
node node_modules/vite/bin/vite.js build

echo "=== DIST CONTENTS ==="
ls -la dist || true
echo "====================="

echo "=== STARTING SERVER ==="
npx --yes serve dist --single --listen tcp://0.0.0.0:${PORT}
