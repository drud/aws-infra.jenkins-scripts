#!/bin/bash -xe

env

# declare -A allsites
# allsites[Sites]=Updates
if [[ $HOSTNAME == "All" ]]
then
  arr=("web02.newmediadenver.com" "web03.newmediadenver.com" "web04.newmediadenver.com" "web05.newmediadenver.com" "web01.nmdev.us" "web03.nmdev.us" "web04.nmdev.us") 
else 
  arr=($HOSTNAME)
fi

for i in "${arr[@]}"
do
  echo -e "\n Checking server: $i\n"
  PRIVATEIP=$(knife search node "name:$i" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
  ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP '
    declare -A sites
    declare -A sites_version
    declare -A sites_updates

    cd /var/www/ && for d in */ ; 
    do 
      site=$(echo $d | sed 's:/*$::')
      version_docroot=$(drush -p5.5 -r /var/www/$d/current/docroot st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
      version_current=$(drush -p5.5 -r /var/www/$d/current st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
      if [[ -n "$version_docroot" || -n "$version_current" ]]; 
        then echo "Checking Drupal $version_docroot$version_current site: $site"; 
          if [[ -n "$version_docroot" ]]; 
            then 
              UPS="$(drush -p5.5 -r /var/www/$d/current/docroot ups 2>/dev/null)" &&
              echo "${UPS}" > /var/tmp/tmp.txt && 
              errors="$(wc -l /var/tmp/tmp.txt | grep -o [0-9][0-9])" &&
              sites[$site]="${UPS}"
              sites_version[$site]=$version_docroot
              sites_updates[$site]=$errors
            else 
              UPS="$(drush -p5.5 -r /var/www/$d/current ups 2>/dev/null)" &&
              echo "${UPS}" > /var/tmp/tmp.txt && 
              errors="$(wc -l /var/tmp/tmp.txt | grep -o [0-9][0-9])" &&
              sites[$site]="${UPS}"
              sites_version[$site]=$version_current
              sites_updates[$site]=$errors
          fi; 
      fi; 
    done
    
    for key in ${!sites[@]}; do
      printf  "Site: %-20s Drupal version: %-20s Available updates: ${sites_updates[${key}]}\n" ${key} ${sites_version[${key}]} ${sites_updates[${key}]}
      #echo "${sites[${key}]}"
    done
    '
done