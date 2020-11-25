#! /usr/bin/env bash

set -e

MOUNT_LOCATION=$1
GPG_MOUNT_LOCATION=$2

MOUNT_LOCATION=$(readlink -f $MOUNT_LOCATION)

docker run --rm \
    -v $MOUNT_LOCATION/repo_files:/share \
    -v $GPG_MOUNT_LOCATION:/root/.gnupg \
    -v $MOUNT_LOCATION/debs_staging:/debs \
    -v /usr/share/apt-repo/scripts:/scripts \
    -it apt-repo add_debs.py