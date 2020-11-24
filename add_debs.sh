#! /usr/bin/env bash

set -e

MOUNT_LOCATION=${1:-$(pwd)}

MOUNT_LOCATION=$(readlink -f $MOUNT_LOCATION)

docker run \
    -v $MOUNT_LOCATION/repo_files:/share \
    -v $MOUNT_LOCATION/gpg:/root/.gnupg \
    -v $MOUNT_LOCATION/debs_staging:/debs \
    -v /opt/apt-repo/scripts:/scripts \
    -it apt-repo add_debs.py