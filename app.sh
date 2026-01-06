#!/usr/bin/env bash
set -e

echo "=== APP.SH STARTED ==="
echo "PWD=$(pwd)"
echo "PORT env='${PORT}'"
env | grep -E 'PORT|DOMINO' || true

cd /repos/LoE-Assistant/loe-frontend

echo "Installing deps..."
npm ci || npm install

echo "Building frontend..."
node node_modules/vite/bin/vite.js build

echo "dist contents:"
ls -la dist

# Domino apps proxy to 8888 by default
APP_PORT=8888
echo "Starting static server on 0.0.0.0:${APP_PORT}"

npx --yes serve dist --single -l tcp://0.0.0.0:${APP_PORT}
