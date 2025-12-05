#!/bin/bash

SCRIPT_DIR="$(dirname "$0")"
LOGFILE="$SCRIPT_DIR/error_log.txt"

/usr/bin/env python3 "$SCRIPT_DIR/gratio_tuner.py" 2>> "$LOGFILE"
status=$?

if [ $status -ne 0 ]; then
    echo "[$(date)] Python crashed (exit code $status)" >> "$LOGFILE"
    echo "The script exited with an error (status $status). Log saved to $LOGFILE."
fi

echo
echo "Press Enter to close..."
read
