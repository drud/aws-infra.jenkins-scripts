#!/bin/bash -xe

env

declare -A allsites

if [[ $HOSTNAME == "All" ]]
then
  arr=("web02.newmediadenver.com" "web03.newmediadenver.com" "web04.newmediadenver.com" "web05.newmediadenver.com" "web01.nmdev.us" "web03.nmdev.us" "web04.nmdev.us") 
else 
  arr=($HOSTNAME)
fi

for i in "${arr[@]}"
do
  echo -e "\nSERVER: $i\n"
  PRIVATEIP=$(knife search node "name:$i" -c ${JENKINS_HOME}/workspace/jenkins-scripts/.chef/knife.rb | sed -n '4p' | awk '{print $2}')
  ssh -A -i /var/jenkins_home/.ssh/aws.pem -o StrictHostKeyChecking=no root@$PRIVATEIP '
    declare -A sites
    cd /var/www/ && for d in */ ; 
    do 
      site=$(echo $d | sed 's:/*$::')
      version_docroot=$(drush -p5.5 -r /var/www/$d/current/docroot st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 
      version_current=$(drush -p5.5 -r /var/www/$d/current st | grep "Drupal version" | grep -o [678][.] | grep -o [678]); 

      if [[ -n "$version_docroot" || -n "$version_current" ]]; 
        then echo "Drupal $version_docroot$version_current Site: $site"; 
          if [[ -n "$version_docroot" ]]; 
            then 
              sites[$site]=$version_docroot
            else 
              sites[$site]=$version_current
          fi; 
      fi; 
    done
    echo -e "\n"
    for key in ${!sites[@]}; do
      echo ${key} ${sites[${key}]}
      allsites+=([${key}]=${sites[${key}]})
    done
    '
done

echo -e "\n allsites:"
for key in ${!allsites[@]}; do
  echo ${key} ${allsites[${key}]}
done

      # if [[ -n "$version_docroot" || -n "$version_current" ]]; 
      #   then echo "Drupal $version_docroot$version_current Site: $site"; 
      #     if [[ -n "$version_docroot" ]]; 
      #       then 
      #         UPS="$(drush -p5.5 -r /var/www/$d/current/docroot ups)" &&
      #         echo "${UPS}" > /var/tmp/tmp.txt && 
      #         errors="$(wc -l /var/tmp/tmp.txt | grep -o [0-9][0-9])" &&
      #         sites[$site]=$errors
      #       else 
      #         UPS="$(drush -p5.5 -r /var/www/$d/current ups)" &&
      #         echo "${UPS}" > /var/tmp/tmp.txt && 
      #         errors="$(wc -l /var/tmp/tmp.txt | grep -o [0-9][0-9])" &&
      #         sites[$site]=$errors
      #     fi; 
      # fi; 