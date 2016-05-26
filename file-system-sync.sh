#!/bin/bash
# 3 Jenkins jobs that pass data to the next
#Sync server - the good server
#Desynced server - the server without data
#GOOD_SERVER="web01.nmdev.us"
#OLD_SERVER="web02.nmdev.us"
IFS=' ' read -r -a array <<< "$string"
#1 . SSH into a good server and pull all the sites and SHAS from /var/www/*/current with find command
echo "Reading webroots and SHAs from known good server."
HOSTNAME=$GOOD_SERVER
WEBROOTS_AND_SHAS=(`eval "$(/var/jenkins_home/workspace/jenkins-scripts/ssh-generator.sh find-web-roots-and-shas.sh env)"`)

HOSTNAME=$OLD_SERVER
# get length of an array
arrlen=${#WEBROOTS_AND_SHAS[@]}
PROBLEM_SITES=()
TRIGGERED_JOBS=()
# 2. Given a site path, find the SHA on the desynced server and pass it back
for (( i=0; i<${arrlen}; i=i+2 )); do
  RET_CODE=0
  WEBROOT=${WEBROOTS_AND_SHAS[i]}
  GOODSHA=${WEBROOTS_AND_SHAS[i+1]}
  BAGNAME=$(echo $WEBROOT | sed 's|/var/www/||' | sed 's|/current||')
  # Now, if the server ends in *.nmdev.us, ENV=staging. If server ends in *.newmediadenver.com, ENV=production.
  if [[ $OLD_SERVER == *"nmdev.us"* ]]; then
    SERVER_ENVIRONMENT="staging"
  else
    SERVER_ENVIRONMENT="production"
  fi
  # 3. Given a site path and a SHA, go to the given path and check the SHA. If the SHA doesn't match the first one, take the site path and parse out /var/www/<THIS DIR NAME> and set that equal to the databag name.  Else, fail
  # Trigger jenkins job: {ENV}-{databag_name}
  echo "Working on '$WEBROOT':"
  SHA_CHECK=(`eval $(/var/jenkins_home/workspace/jenkins-scripts/ssh-generator.sh "check-sha.sh $WEBROOT $GOODSHA" env)`)
  if [ "${SHA_CHECK[0]}" == "NOT" -a "${SHA_CHECK[1]}" == "FOUND" ]; then
    echo -e "\tFolder '$WEBROOT' NOT FOUND"
    echo "Triggering an update on Jenkins job $SERVER_ENVIRONMENT-$BAGNAME to correct directory structure..."
    python -u /var/jenkins_home/workspace/jenkins-scripts/jenkins-callback-wrapper.py --environment $SERVER_ENVIRONMENT --chef-action update --bag-name $BAGNAME
    RET_CODE=$?
  else
    echo -e "\tCorrect SHA:\t$GOODSHA"
    echo -e "\tFound SHA:\t${SHA_CHECK[0]}"
    echo -e "\tMatch?\t${SHA_CHECK[1]}"
    if [[ "${SHA_CHECK[1]}" != "MATCH" ]]; then
      echo "Non-matching directory structure"
      echo "Triggering an update on Jenkins job $SERVER_ENVIRONMENT-$BAGNAME to correct directory structure..."
      python -u /var/jenkins_home/workspace/jenkins-scripts/jenkins-callback-wrapper.py --environment $SERVER_ENVIRONMENT --chef-action update --bag-name $BAGNAME
      RET_CODE=$?
    else
      echo "Match confirmed. Moving along..."
      RET_CODE=3
    fi
  fi
  if [ "$RET_CODE" -eq 1 ]; then
    echo "Adding problem site to array"
    PROBLEM_SITES+=("$BAGNAME")
  elif [ "$RET_CODE" -eq 0 ]; then
    echo "Remembering this job as a success."
    TRIGGERED_JOBS+=("$SERVER_ENVIRONMENT-$BAGNAME")
  fi
done
if [ -z "$PROBLEM_SITES" ]; then
  echo "All done. No problems :-)"
  echo "Here are the jobs that were triggered."
  for JOB in $TRIGGERED_JOBS; do
    echo -e "\t-$JOB"
  done
  exit 0
fi
# If there are any values in problem sites, list them here.
echo "Here are the sites we had issues syncing (debug output available above):"
for SITE in $PROBLEM_SITES; do
  echo -e "\t-$SITE"
done
# If we got here, then there was obviously an issue. Return a bad status code and FAIL THE JOB!
exit 1



