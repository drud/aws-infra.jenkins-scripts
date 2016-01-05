#!/bin/bash -xe
env
COUNT="$COUNT"
PRIVATEIP=$(knife search node "name:$HOSTNAME" --config ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP cleanup-releases-exec.sh $COUNT