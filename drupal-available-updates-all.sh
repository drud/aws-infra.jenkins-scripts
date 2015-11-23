#!/bin/bash -xe

env

if [[ $HOSTNAME == "All" ]]
then
  arr=("web02.newmediadenver.com" "web03.newmediadenver.com" "web04.newmediadenver.com" "web05.newmediadenver.com" "web01.nmdev.us" "web03.nmdev.us" "web04.nmdev.us") 
else 
  arr=($HOSTNAME)
fi

if [[ -n "$SINGLE_SITE_NAME" ]];
  CHEF_ENVIRONMENT=$SINGLE_SITE_ENVIRONMENT
  then
    PRIVATEIP=$(knife search node "chef_environment:$CHEF_ENVIRONMENT AND nmd$SINGLE_SITE_NAME:action" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
    ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP "DETAILS=$DETAILS SITE_NAME=$SINGLE_SITE_NAME CHEF_ENVIRONMENT=$CHEF_ENVIRONMENT" '
      cd /var/www/$SITE_NAME
      site=$SITE_NAME
      d=$SITE_NAME
      version_docroot=$(drush -p5.5 -r /var/www/$d/current/docroot st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
      version_current=$(drush -p5.5 -r /var/www/$d/current st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
      if [[ -n "$version_docroot" || -n "$version_current" ]]; 
        then
          if [[ -n "$version_docroot" ]]; 
            then 
              UPS="$(drush -p5.5 -r /var/www/$d/current/docroot ups 2>/dev/null)" &&
              version=$version_docroot
            else 
              UPS="$(drush -p5.5 -r /var/www/$d/current ups 2>/dev/null)" &&
              version=$version_current 
          fi;
          updates=$(grep -ci "update" <<< "$UPS") &&
          echo "Checking Drupal $version site: $site in $CHEF_ENVIRONMENT $has $updates updates available" &&
          if [[ $DETAILS = true ]]; then echo -e "${UPS}" "\n"; fi;
      fi; 
    '
else
  for i in "${arr[@]}"
  do
    echo -e "\n Checking server: $i\n"
    PRIVATEIP=$(knife search node "name:$i" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
    ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP "DETAILS=$DETAILS SERVER=$i" '
      cd /var/www/ && for d in */ ; 
      do 
        site=$(echo $d | sed 's:/*$::')
        version_docroot=$(drush -p5.5 -r /var/www/$d/current/docroot st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
        version_current=$(drush -p5.5 -r /var/www/$d/current st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
        if [[ -n "$version_docroot" || -n "$version_current" ]]; 
          then
            if [[ -n "$version_docroot" ]]; 
              then 
                UPS="$(drush -p5.5 -r /var/www/$d/current/docroot ups 2>/dev/null)" &&
                version=$version_docroot
              else 
                UPS="$(drush -p5.5 -r /var/www/$d/current ups 2>/dev/null)" &&
                version=$version_current 
            fi;
            updates=$(grep -ci "update" <<< "$UPS") &&
            echo "Checking Drupal $version site: $site on server: $SERVER has $updates updates available" &&
            if [[ $DETAILS = true ]]; then echo -e "${UPS}" "\n"; fi;
        fi; 
      done'
  done
fi