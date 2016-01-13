#!/bin/bash -xe
env
COUNT="$COUNT"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$HOSTNAME "bash -s --" < ${JENKINS_HOME}/workspace/jenkins-scripts/cleanup-releases-exec.sh $COUNT