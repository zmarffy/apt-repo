#!/bin/bash

set -e

pip install -e .
cat << "EOF" >> "$HOME/.bashrc"
if [ -f "$HOME/.promptedenv" ]; then
    source "$HOME/.promptedenv"
fi
EOF
