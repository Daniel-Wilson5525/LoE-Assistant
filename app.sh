#!/usr/bin/env bash
set -e

cd /repos/LoE-Assistant/loe-frontend

npm install --include=optional

# Build (using node directly avoids permission issues)
node node_modules/vite/bin/vite.js build

# Serve on Domino’s required port
npx --yes serve dist --single -l tcp://0.0.0.0:${PORT}
