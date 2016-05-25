#!/bin/bash
# 3 Jenkins jobs that pass data to the next
#Sync server - the good server
#Desynced server - the server without data
GOOD_SERVER="web01.nmdev.us"
OLD_SERVER="web02.nmdev.us"
IFS=' ' read -r -a array <<< "$string"
#1. SSH into a good server and pull all the sites and SHAS from /var/www/*/current with find command
HOSTNAME=$GOOD_SERVER
WEBROOTS_AND_SHAS=(`eval "$(./ssh-generator.sh find-web-roots-and-shas.sh env)"`)

HOSTNAME=$OLD_SERVER
# get length of an array
arrlen=${#WEBROOTS_AND_SHAS[@]}
 
# use for loop read all nameservers
for (( i=0; i<${arrlen}; i=i+2 )); do
  WEBROOT=${WEBROOTS_AND_SHAS[i]}
  GOODSHA=${WEBROOTS_AND_SHAS[i+1]}
done

#2. Given a site path, find the SHA on the desynced server and pass it back
SHA_CHECK=$(./ssh-generator.sh "check-sha.sh $WEBROOT $GOODSHA" env)

#3. Given a site path and a SHA, go to the given path and check the SHA. If the SHA doesn't match the first one, take the site path and parse out /var/www/<THIS DIR NAME> and set that equal to the databag name. Now, if the server ends in *.nmdev.us, ENV=staging. If server ends in *.newmediadenver.com, ENV=production. Else, fail
#Trigger jenkins job: {ENV}-{databag_name}