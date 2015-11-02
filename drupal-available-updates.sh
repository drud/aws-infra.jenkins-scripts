#!/bin/bash -xe

env

if [ $HOSTNAME -ne 'All']; then
  PRIVATEIP=$(knife search node "name:$HOSTNAME" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
  #PRIVATEIP=$(knife search node "chef_environment:$CHEF_ENVIRONMENT AND $COOKBOOK_NAME:action" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
  ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP '
    cd /var/www/ && for d in */ ; 
      do 
        version_docroot=$(drush -p5.5 -r /var/www/$d/current/docroot st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
        version_current=$(drush -p5.5 -r /var/www/$d/current st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 

        if [[ -n "$version_docroot" || -n "$version_current" ]]; 
          then echo "Drupal $version_docroot $version_current Site: $d"; 
            if [[ -n "$version_docroot" ]]; 
              then drush -p5.5 -r /var/www/$d/current/docroot ups; 
              else  drush -p5.5 -r /var/www/$d/current ups; 
            fi; 
        fi; 
      done'
fi