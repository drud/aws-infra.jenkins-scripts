#!/bin/bash

# Available variables
#SRC_SERVER
#DEST_SERVER
echo "Source:"
echo $SRC_SERVER
echo "Dest:"
echo $DEST_SERVER
# Prerequisites
# We are SSH-ed into a remote host and calling this script on that host
# Communication on Port 22 is available
# The standard ubuntu AWS deploy key has been placed at /tmp/aws.pem
chmod 0400 /tmp/aws.pem

# Call rsync on the different nodes.
rsync -F --compress --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" ubuntu@$SRC_SERVER:/etc/nginx/sites-available /etc/nginx/
rsync -F --compress --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" ubuntu@$SRC_SERVER:/etc/nginx/sites-enabled /etc/nginx/
rsync -F --compress --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" ubuntu@$SRC_SERVER:/var/www/ /var/

# Remove the SSH key
rm -rf /tmp/aws.pem