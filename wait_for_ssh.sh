#!/bin/bash
if [ -z "$1" ]; then
  echo "This script requires that you pass in a server name to poll."
  echo "Usage: ./wait_for_ssh.sh SERVER_NAME"
  exit 1;
fi
SERVER_NAME=$1

# Wait for the SSH server to become available
echo "Waiting for the SSH to be available"
ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 $SERVER_NAME
while test $? -gt 0
do
   sleep 5 # highly recommended - if it's in your local network, it can try an awful lot pretty quick...
   echo "Trying again..."
   ssh -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 $SERVER_NAME 
done
echo "SSH is now available."