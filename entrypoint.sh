#!/bin/sh

set -e

if [ -n "$GH_TOKEN" ]; then
    gh auth setup-git
fi

if [ -n "$SET_UP_GITCONFIG" ]; then
    git config --global user.email "$GIT_EMAIL"
    git config --global user.name "$GIT_USERNAME"
fi

exec "$@"
