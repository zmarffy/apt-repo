#!/bin/sh

if [ -n "$GH_TOKEN" ]; then
    gh auth setup-git
fi

git config --global user.email "$GIT_EMAIL"
git config --global user.name "$GIT_USERNAME"

exec "$@"
