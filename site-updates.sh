#!/bin/bash -xe
if [ -z "$COOKBOOK_NAME" ]; then
  export COOKBOOK_NAME="nmd$JOB_NAME"
fi

env

PRIVATEIP=$(knife search node "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP 'chef-client -l debug' 