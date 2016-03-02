#!/bin/bash
if [ -z "$1" ]; then
  echo "This script requires that you pass in an OS to run."
  echo "Usage: ./security-upgrade-remote.sh $OS"
  exit 1;
fi
OS="$1"
function apt_package_exists() {
  return dpkg -l "\$1" &> /dev/null
}
function yum_package_exists() {
  if yum list installed "\$1" &>/dev/null; then
    true
  else
    false
  fi
}

if [ "$OS" = "UBUNTU" ]; then
  # Ubuntu/Debian
  if ! apt_package_exists unattended-upgrade ; then
    apt-get -y update &&
    echo unattended-upgrades unattended-upgrades/enable_auto_updates boolean true | debconf-set-selections &&
    apt-get -y install unattended-upgrades &&
    dpkg-reconfigure -f noninteractive unattended-upgrades;
  fi

  unattended-upgrade -v

else
  # CentOs
  if ! yum_package_exists yum-plugin-security ; then
      yum install -y yum-plugin-security
  fi

  yum update -y --security;
fi


