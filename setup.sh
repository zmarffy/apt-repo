#! /usr/bin/env bash

set -e

MOUNT_LOCATION=$1
GPG_MOUNT_LOCATION=$2
ORIGIN=$3
LABEL=$4
CODENAME=$5
ARCH=$6
COMPONENTS=$7
DESC=$8

if [[ -z "$MOUNT_LOCATION" ]]; then
    echo "Missing params"
    exit 1
fi

MOUNT_LOCATION=$(readlink -f $MOUNT_LOCATION)

echo "-> Working..."

docker build . -t apt-repo \
    --build-arg origin="$ORIGIN" \
    --build-arg label="$LABEL" \
    --build-arg codename="$CODENAME" \
    --build-arg arch="$ARCH" \
    --build-arg components="$COMPONENTS" \
    --build-arg description="$DESC" \
    > /dev/null

if [[ ! -d "$GPG_MOUNT_LOCATION" ]]; then
    echo "-> Create GPG key"
    docker run --rm \
        -v $MOUNT_LOCATION/repo_files:/share \
        -v $GPG_MOUNT_LOCATION:/root/.gnupg \
        -v /usr/share/apt-repo/scripts:/scripts \
        -it apt-repo create_key.py
fi
echo "-> Setup repo"
docker run --rm \
    -v $MOUNT_LOCATION/repo_files:/share \
    -v $GPG_MOUNT_LOCATION:/root/.gnupg \
    -v /usr/share/apt-repo/scripts:/scripts \
    -it apt-repo setup_repo.py