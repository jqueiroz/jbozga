#!/usr/bin/env bash
set -e

CONFIG_FILENAME="$1"
if [ -z "$CONFIG_FILENAME" ]; then
    echo "Error: expected a single argument with the path to the xmobar config."
    echo "Example: run-jbozga-xmobar.sh /path/to/xmobar-config.hs"
    exit 1
fi

xmobar "$CONFIG_FILENAME"
