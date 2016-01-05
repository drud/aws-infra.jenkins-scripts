#!/bin/bash -xe
env
COUNT="$COUNT"
PRIVATEIP=$(knife search node "name:$HOSTNAME" | sed -n '6p' | awk '{print $2}')
ssh -p22 -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP cleanup-releases-exec.sh $COUNT