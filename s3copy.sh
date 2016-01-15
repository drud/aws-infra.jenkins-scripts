#!/bin/bash -xe
env
S3ARGS="-k ${AWS_ACCESS_KEY} -sk ${AWS_SECRET_KEY}"
LATEST=$(sudo s3latest $S3ARGS nmdarchive $sitename/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
sudo s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO
