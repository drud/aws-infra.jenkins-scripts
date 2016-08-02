#!/bin/bash
if [ -z "$1" -o -z "$2" ]; then
  echo "This script requires that you pass in the src server and dest server to run."
  echo "Usage: ./rsync.sh SRC_SERVER DEST_SERVER"
  exit 1;
fi
SRC_SERVER=$1
DEST_SERVER=$2
# Available variables
#SRC_SERVER
#DEST_SERVER
echo "Source: (where we are)"
echo $SRC_SERVER
echo "Dest:"
echo $DEST_SERVER
# Prerequisites
# We are SSH-ed into a remote host and calling this script on that host
# Communication on Port 22 is available
# The standard ubuntu AWS deploy key has been placed at /tmp/aws.pem
chmod 0400 /tmp/aws.pem

# Call rsync on the different nodes.
# echo "Copying /etc/nginx/sites-enabled..."
# rsync -F --compress --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" /etc/nginx/sites-available ubuntu@$DEST_SERVER:/etc/nginx/
# echo "Copying /etc/nginx/sites-available..."
# rsync -F --compress --archive --progress --stats --rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' --rsync-path="sudo rsync" /etc/nginx/sites-enabled ubuntu@$DEST_SERVER:/etc/nginx/

for WEB_ROOT in $(find /var/www -maxdepth 2 -type l -name current -print); do
    # Sample WEB_ROOT - /var/www/histco/current
    # Sample CURRENT_RELEASE - /var/www/histco/releases/20160722223438
    CURRENT_RELEASE="$(readlink -f $WEB_ROOT)"
    BAGNAME=$(echo $WEB_ROOT | sed 's|/var/www/||' | sed 's|/current||')
    echo "Working on $BAGNAME..."
    # Copy the release
    rsync \
	-F \
	--compress \
	--archive \
	--progress \
	--stats \
	--rsh 'ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no' \
	--rsync-path="sudo mkdir -p /var/www/$BAGNAME/releases && sudo rsync" \
	--include */
	--exclude .git/ \
	$CURRENT_RELEASE ubuntu@DEST_SERVER:/var/www/$BAGNAME/releases/
    # Copy (or recreate) the current symlink - remember, you are on the src host now
    ssh -i /tmp/aws.pem -o StrictHostKeyChecking=no ubuntu@DEST_SERVER "ln -s $CURRENT_RELEASE /var/www/$BAGNAME/current"
done

# Remove the SSH key
rm -rf /tmp/aws.pem