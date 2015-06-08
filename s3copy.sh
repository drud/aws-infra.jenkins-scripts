#!/bin/bash -xe
env
S3ARGS="-k ${AWS_ACCESS_KEY} -sk ${AWS_SECRET_KEY}"
PRIVATEIP=$(knife search node "chef_environment:staging AND roles:web2" --config /var/jenkins_home/workspace/jenkins-chef-client/.chef/knife.rb | sed -n '6p' | awk '{print $2}')
LATEST=$(ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP s3latest $S3ARGS nmdarchive $sitename/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO