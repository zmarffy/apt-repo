#! /usr/bin/env bash

if [[ ! -z "$REPO_PASSWORD" ]]; then
    htpasswd -b -c passwd/passwords repo ${REPO_PASSWORD}
    mv /usr/local/apache2/conf/httpd_auth.conf /usr/local/apache2/conf/httpd.conf
else
    rm -r passwd
    rm /usr/local/apache2/conf/httpd_auth.conf
fi
httpd-foreground