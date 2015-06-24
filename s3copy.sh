#!/bin/bash -xe
env
S3ARGS="-k ${AWS_ACCESS_KEY} -sk ${AWS_SECRET_KEY}"
PRIVATEIP=$(knife exec -E "nodes.find('chef_environment:staging AND roles:web2') { |n| puts n.name }" -c ${JENKINS_HOME}/workspace/jenkins-chef-client/.chef/knife.rb | sed -n '1p' | awk '{print $1}')
LATEST=$(ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP s3latest $S3ARGS nmdarchive $sitename/$from)
S3FROM="s3://nmdarchive/${LATEST}"
S3TO=`echo $S3FROM | sed s/$from/$to/`
ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP s3copy $S3ARGS -n 8 -s 100 -f $S3FROM $S3TO