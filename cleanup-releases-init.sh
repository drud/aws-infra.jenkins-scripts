#!/bin/bash -xe
env
COUNT="$COUNT"
RESULT=(`eval $(/var/jenkins_home/workspace/jenkins-scripts/ssh-generator.sh "cleanup-releases-exec.sh $COUNT" env)`)
echo $RESULT