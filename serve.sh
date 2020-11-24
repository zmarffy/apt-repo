#! /usr/bin/env bash

set -e

MOUNT_LOCATION=${1:-$(pwd)}
PORT=${2:-8080}

MOUNT_LOCATION=$(readlink -f $MOUNT_LOCATION)

docker run --rm -d --name apt-repo -p $PORT:80 -v $MOUNT_LOCATION/repo_files:/usr/local/apache2/htdocs/ httpd
