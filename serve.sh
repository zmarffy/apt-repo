#! /usr/bin/env bash

set -e

MOUNT_LOCATION=$1
PORT=$2
NAME=$3

MOUNT_LOCATION=$(readlink -f $MOUNT_LOCATION)

docker run --rm -d --name apt-repo_$NAME -p $PORT:80 -v $MOUNT_LOCATION/repo_files:/usr/local/apache2/htdocs/ httpd
