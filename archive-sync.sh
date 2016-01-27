#!/bin/bash -xe
env
if [ $direction = "up" ]; then
   from="_default"
   to="production"
else
  from="production"
  to="_default"
fi

S3ARGS="-k ${AWS_ACCESS_KEY} -sk ${AWS_SECRET_KEY}"
LATEST=$(sudo s3latest $S3ARGS nmdarchive $sitename/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
STAGINGTO=`echo $S3FROM | sed s/$from/staging/`
sudo s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO
sudo s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $STAGINGTO
