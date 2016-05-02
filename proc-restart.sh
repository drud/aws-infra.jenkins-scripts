#!/bin/bash
# Must pass $PROCNAME, HOSTNAME, OS into the env.
if [ -z "$PROCNAME" ]; then
	echo "PROCNAME is undefined"
	exit 1;
fi
IFS="%"
function proc_count (){
	local PROC=$1
	local PROC_LIST_CMD='ps aux | grep "$PROC"'
	local PROC_LIST=`eval $PROC_LIST_CMD`
	echo "Processes matching '$PROC':"
	echo $PROC_LIST
	NUM_PROCS=`pgrep $PROC | wc -l`
	echo "Number of '$PROC' processes found (excluding grep lines): $NUM_PROCS"
}
echo "--------------"
proc_count "$PROCNAME"
# By default, we want to perform a restart
OP="restart"
# BUT if $FORCEOP is set
if [ "$FORCEOP" != "no" ]; then
	echo "Setting operation to '$FORCEOP'"
	OP=$FORCEOP
fi
# Build the commands out
if [ "$OS" = "CENTOS" ]; then
	CMD="/etc/init.d/$PROCNAME $OP"
else
	CMD="service $PROCNAME $OP"
fi

# Override the cmd if hard reset set
if [ "FORCEOP" = "hard reset" ]; then
	echo "A hard reset of proc $PROCNAME has been specified."
	CMD="service $PROCNAME stop; killall $PROCNAME; service $PROCNAME start"
fi

if [ $NUM_PROCS -lt 1 -a "$FORCEOP" = "no" ]; then
	echo "No matching process found! Restarting '$PROCNAME'..."
	eval $CMD
elif [ "$FORCEOP" != "no" ]; then
	echo "Performing '$CMD'"
	eval $CMD
else
	echo "Found $NUM_PROCS running processes - We're good...right?"
fi
echo "--------------"
unset IFS