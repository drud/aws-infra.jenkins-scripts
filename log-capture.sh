#!/bin/bash -xe
FILENAME=$(hostname)-$(date +%s)-error-log.tar.gz
# zip and upload
tar -czf /tmp/$FILENAME /var/log/nginx;
s3upload -l DEBUG -k AWS_ACCESS_KEY -sk AWS_SECRET_KEY -f -np 8 -s 100 $FILENAME s3://nmdarchive/error-log/$FILENAME;
# purge logs from server
find /var/log/nginx -type f -exec sh -c '>{}' \;
# remove the archive
rm /tmp/$FILENAME;
