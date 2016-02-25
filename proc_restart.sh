#!/bin/bash
# Must pass $PROCNAME, HOSTNAME into the env.
# PROCNAME=""
IFS="%"
proc_count (){
	local PROC=$1
	local PROC_LIST_CMD='ps aux | grep "$PROC"'
	local PROC_LIST=`eval $PROC_LIST_CMD`
	echo "Processes matching '$PROC':"
	echo $PROC_LIST
	NUM_PROCS=`pgrep $PROC | wc -l`
	echo "Number of '$PROC' processes found: $NUM_PROCS"
}
sudo -i
proc_count "$PROCNAME"
OS=$(./determine_os.sh)
if [ "$OS" = "CENTOS" ]; then
	RESTART_CMD="/etc/init.d/$PROCNAME restart"
else
	RESTART_CMD="service $PROCNAME restart"
fi

if [ $NUM_PROCS -lt 1 ]; then
	echo "No matching process found! Restarting '$PROCNAME'..."
	eval $RESTART_CMD
else
	echo "Found $NUM_PROCS running processes - We're good...right?"
fi
unset IFS