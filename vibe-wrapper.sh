#!/bin/bash
# Vibe CLI Wrapper - Ensures proper environment activation

# Get the directory where this script is located (resolving symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Run vibe with uv from the project directory
cd "$SCRIPT_DIR" && exec uv run python vibe "$@"