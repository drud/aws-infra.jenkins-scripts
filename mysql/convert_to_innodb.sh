#!/bin/bash

#!!! Pass these variables in
ENVIRONMENT="staging"


# Setup the SQL variables ########################
# Do this on each node first.
DESYNC_NODE="SET GLOBAL wsrep_OSU_method='RSU';"

# Find all the myisam tables
FIND_ALL_TABLES="SELECT table_schema, TABLE_NAME, table_rows FROM information_schema.TABLES WHERE engine='myisam' AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql');"

# Change a myisam table to InnoDB
CHANGE_TABLE="ALTER TABLE dbname.table_name engine = InnoDB;"

# Do this on each node to finish it off.
SYNC_NODE="SET GLOBAL wsrep_OSU_method='TOI';"
##################################################
if [ "$ENVIRONMENT" = "production" ]; then
  PERCONA_SERVERS=("percona04.newmediadenver.com" "percona05.newmediadenver.com" "percona06.newmediadenver.com")
  PRIMARY_SERVER="percona04.newmediadenver.com"
  OS="UBUNTU"
elif [ "$ENVIRONMENT" = "staging" ]; then
  PERCONA_SERVERS=("percona03.nmdev.us")
  PRIMARY_SERVER="percona03.nmdev.us"
  OS="CENTOS"
else
  echo "Unrecognized environment of '$ENVIRONMENT'"
fi
###################################################

# Find all DBs that need to be converted
SCRIPT="mysql -u doer -pYxPyixXLUEtFUR3z -e \\\"$FIND_ALL_TABLES\\\" 2>/dev/null"
SSH_CMD="$($JENKINS_SCRIPTS/ssh-generator.sh "$SCRIPT" "NOFILE" $PRIMARY_SERVER $OS)"
echo "$SSH_CMD"
RET=$($SSH_CMD)
STATUS=$?
echo $STATUS
echo $RET
exit $STATUS


for HOST in ${PERCONA_SERVERS[@]}; do
  # Do this on each node first.
  if [ "$HOST" = "$PRIMARY_SERVER" ]; then
    echo ""
  else
    echo ""
  fi
  SCRIPT='$JENKINS_SCRIPTS/mysql/mysql_command_injector.sh "SELECT * FROM THIS;" "DB_NAME"'
  SSH_CMD=$($JENKINS_SCRIPTS/ssh-generator.sh "$SCRIPT" env $HOST $OS)
  echo $SSH_CMD
done