#!/bin/bash

set -e

if [ ! -d ".venv" ]; then
    poetry config virtualenvs.in-project true && POETRY_DYNAMIC_VERSIONING_COMMANDS="" poetry install
fi
