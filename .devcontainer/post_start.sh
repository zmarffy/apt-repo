#!/bin/bash

set -e

ask_for_env_vars_and_dump_them_to_dotenv()
{
    for v in "${VARS[@]}"; do
        if [ -z "${!v}" ]; then
            printf "%q" "$v"= >> "$HOME/.promptedenv"
            read -p "Enter $v: " "$v"
            printf "%q\n" "${!v}" >> "$HOME/.promptedenv"
        fi
    done
}

VARS=("GH_TOKEN")

ask_for_env_vars_and_dump_them_to_dotenv
source "$HOME/.promptedenv"
sh /entrypoint.sh
