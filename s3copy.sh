#!/bin/bash -xe
env
S3ARGS="-k ${AWS_ACCESS_KEY} -sk ${AWS_SECRET_KEY}"
PRIVATEIP=$(knife exec -E "nodes.find('chef_environment:staging AND roles:web2') { |n| puts n.name }" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '1p' | awk '{print $1}')
LATEST=$(s3latest $S3ARGS nmdarchive $sitename/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO
