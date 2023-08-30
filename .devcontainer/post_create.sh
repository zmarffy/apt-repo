#!/bin/bash

set -e

POETRY_DYNAMIC_VERSIONING_COMMANDS="" poetry install
cat << "EOF" >> "$HOME/.bashrc"
if [ -f "$HOME/.promptedenv" ]; then
    source "$HOME/.promptedenv"
fi
EOF
