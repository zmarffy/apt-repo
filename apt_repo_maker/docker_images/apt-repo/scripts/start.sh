#! /usr/bin/env bash

set -e

# Fix vars
USE_SSL=$(echo $USE_SSL | sed -e 's/\(.*\)/\L\1/')
if [ "$USE_SSL" == "true" ]; then
    USE_SSL=true
else
    USE_SSL=false
fi
SERVER_ADMIN_EMAIL=$(echo "${SERVER_ADMIN_EMAIL}" | sed -e 's/[]$.*[\^]/\\&/g' )

# Set auth
if [[ ! -z "$REPO_PASSWORD" ]]; then
    # Set the single basic auth user
    htpasswd -b -c passwd/passwords repo ${REPO_PASSWORD}
    mv /usr/local/apache2/conf/httpd_auth.conf /usr/local/apache2/conf/httpd.conf
else
    rm -rf passwd
    rm -f /usr/local/apache2/conf/httpd_auth.conf
fi

# Set ServerAdmin
sed -i \
    -e "s/^\(ServerAdmin you@example.com\)/ServerAdmin ${SERVER_ADMIN_EMAIL}/" \
    conf/httpd.conf

if $USE_SSL; then
    # Make sure SSL modules are loaded
    sed -i \
        -e 's/^#\(Include .*httpd-ssl.conf\)/\1/' \
        -e 's/^#\(LoadModule .*mod_ssl.so\)/\1/' \
        -e 's/^#\(LoadModule .*mod_socache_shmcb.so\)/\1/' \
        conf/httpd.conf

    # Make sure correct key and cert are grabbed
    sed -i \
        -e 's/\(SSLCertificateFile "\/usr\/local\/apache2\/conf\/\)/SSLCertificateFile "\/usr\/local\/apache2\/mounted\//' \
        -e 's/\(SSLCertificateKeyFile "\/usr\/local\/apache2\/conf\/\)/SSLCertificateKeyFile "\/usr\/local\/apache2\/mounted\//' \
        conf/extra/httpd-ssl.conf
fi

# Inform
echo "=> Preliminary configuration complete"

# Run the server
httpd-foreground