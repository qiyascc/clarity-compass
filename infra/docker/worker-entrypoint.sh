#!/bin/sh
set -e
# Chromium runs headed so sites that turn away headless browsers serve the real page.
if [ -z "$DISPLAY" ]; then
    Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp >/dev/null 2>&1 &
    export DISPLAY=:99
fi
exec "$@"
