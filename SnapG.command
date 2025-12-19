#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOGFILE="$SCRIPT_DIR/error_log.txt"

/usr/bin/env python3 "$SCRIPT_DIR/src/main.py" 2>> "$LOGFILE"
status=$?

if [ $status -ne 0 ]; then
    echo "[$(date)] Python crashed (exit code $status)" >> "$LOGFILE"
    osascript -e 'display alert "SnapG Error" message "SnapG failed to start. See error_log.txt for details."'
fi