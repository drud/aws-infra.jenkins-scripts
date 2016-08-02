#!/bin/bash
if [ -z "$1" -o -z "$2" ]; then
  echo "This script requires that you pass in the src server and dest server to run."
  echo "Usage: ./file-system-rsync.sh SRC_SERVER DEST_SERVER"
  exit 1;
fi
SRC_SERVER=$1
DEST_SERVER=$2
# Place the SSH key on the DEST server for consumption by the rsync script
rsync --rsh 'ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" /var/jenkins_home/.ssh/aws.pem ubuntu@$DEST_SERVER:/tmp/aws.pem 

# Set the HOSTNAME for the ssh-generator
HOSTNAME=$DEST_SERVER

# Call the script and record the results
SCRIPT_RESULTS=$(/var/jenkins_home/workspace/jenkins-scripts/ssh-generator.sh "rsync.sh $SRC_SERVER $DEST_SERVER" env)
echo $SCRIPT_RESULTS