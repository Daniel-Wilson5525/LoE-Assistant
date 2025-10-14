#!/usr/bin/env bash
set -e
exec gunicorn -c services/gunicorn.conf.py services.app:app
