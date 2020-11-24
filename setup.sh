#! /usr/bin/env bash

set -e

MOUNT_LOCATION=$1
ORIGIN=$2
LABEL=$3
CODENAME=$4
ARCH=$5
COMPONENTS=$6
DESC=$7

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
echo "-> Create GPG key"
docker run \
    -v $MOUNT_LOCATION/repo_files:/share \
    -v $MOUNT_LOCATION/gpg:/root/.gnupg \
    -v /opt/apt-repo/scripts:/scripts \
    -it apt-repo create_key.py
echo "-> Setup repo"
docker run -v $MOUNT_LOCATION/repo_files:/share \
    -v $MOUNT_LOCATION/gpg:/root/.gnupg \
    -v /opt/apt-repo/scripts:/scripts \
    -it apt-repo setup_repo.py