#! /usr/bin/env bash

set -e

dir=$(mktemp -d)
dpkg -x "$1" "$dir"
dpkg --info $1 | awk '/Architecture/ {printf "%s", $2}'
rm -rf "$dir"
