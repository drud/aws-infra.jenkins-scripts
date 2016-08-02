#!/bin/bash

# Available variables
#SRC_SERVER
#DEST_SERVER

rsync -F --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path=\"sudo rsync\" ubuntu@$SRC_SERVER:/etc/nginx/sites-available /etc/nginx/
rsync -F --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path=\"sudo rsync\" ubuntu@$SRC_SERVER:/etc/nginx/sites-enabled /etc/nginx/
rsync -F --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path=\"sudo rsync\" ubuntu@$SRC_SERVER:/var/www/ /var/

# Remove the SSH key
rm -rf /tmp/aws.pem