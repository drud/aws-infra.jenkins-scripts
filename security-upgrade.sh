#!/bin/bash
#HOST="monitor01.nmdev.us"
#USER=""

# Try an SSH command to ubuntu first (faster that if root first)
RETURN=$(ssh -q -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no -o NumberOfPasswordPrompts=0 ubuntu@$HOSTNAME 'exit')
if [ $? -eq 0 ]; then
  USER="ubuntu"
  UP_CMD="sudo -i
  unattended-upgrade -v"
else
  USER="root"
  UP_CMD="yum update -y --security;"
fi
ssh -q -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no $USER@$HOSTNAME <<EOF
  $(echo $UP_CMD)
EOF