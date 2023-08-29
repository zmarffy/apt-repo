#!/bin/bash

set -e

poetry install
cat << "EOF" >> "$HOME/.bashrc"
if [ -f "$HOME/.promptedenv" ]; then
    source "$HOME/.promptedenv"
fi
EOF
