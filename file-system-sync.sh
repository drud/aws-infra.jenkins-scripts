#!/bin/bash
# 3 Jenkins jobs that pass data to the next
#Sync server - the good server
#Desynced server - the server without data
GOOD_SERVER="web01.nmdev.us"
OLD_SERVER="web02.nmdev.us"
IFS=$'\n' read -rd '' -a y <<<"$x";
#1. SSH into a good server and pull all the sites and SHAS from /var/www/*/current with find command
HOSTNAME=$GOOD_SERVER
WEBROOTS_AND_SHAS=`eval "$(./ssh-generator.sh find-web-roots-and-shas.sh env)"`

HOSTNAME=$OLD_SERVER
for i in {0..${#WEBROOTS_AND_SHAS[@]}..2}; do
  echo "Record:"
  echo ${WEBROOTS_AND_SHAS[i]}
  echo ${WEBROOTS_AND_SHAS[i+1]}
done

for ROOT_SHA in $WEBROOTS_AND_SHAS; do
  echo "Before"
  echo $ROOT_SHA
  echo "After"
done

#2. Given a site path, find the SHA on the desynced server and pass it back
GOOD_SHA=$(./ssh-generator.sh "check-sha.sh $WEBROOT $SHA" env)

#3. Given a site path and a SHA, go to the given path and check the SHA. If the SHA doesn't match the first one, take the site path and parse out /var/www/<THIS DIR NAME> and set that equal to the databag name. Now, if the server ends in *.nmdev.us, ENV=staging. If server ends in *.newmediadenver.com, ENV=production. Else, fail
#Trigger jenkins job: {ENV}-{databag_name}