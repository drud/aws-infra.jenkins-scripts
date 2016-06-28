# Percona stand-up slave
import subprocess


def build_and_run_command(user, host, command):
  ssh_cmd = ['ssh', '-p22', '-i', aws_key]
  ssh_cmd += ['-o', 'StrictHostKeyChecking=no']
  ssh_cmd += ["{user}@{host}".format(user=user,host=host)]
  ssh_cmd += "mysql "
  ssh_cmd += 'sudo -i {command}'.format(command=command).split(" ")
  try:
    return subprocess.check_output(ssh_cmd, stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    # Gracefully handle previously stopped procs
    if "stop: Unknown instance" in e.output:
      return ""
    elif "no process found" in e.output or "no process killed" in e.output:
      return ""
    elif "command not found" in e.output:
      return "command not found"
    elif "/etc/init.d/glusterfs-server: No such file or directory" in e.output:
      return "command not found"
    exit(e.output)


def mysql_command(command, host):
  "mysql -u -p -h -P"
  print command

def shell_command(command, host):
  print command

#setup the new instance using a pre-built AMI and have the empty DB.
####aws_instance.create_instance_like OR Jenkins

#####Set the 'server_id' variable like we talked about.
# /etc/mysql/my.cnf
# >>>>>>
# # REPLICATION SPECIFIC
# #server_id must be unique across all mysql servers participating in replication.
# server_id = 239
# <<<<<< (from percona04)
# rand int from 0 to 4294967295 that is not 239


# Issue the "change master to " command on the slave, but don't start replication with "start slave" yet.
master="percona03.nmdev.us"
slave=""

# Allow a slave to replicate
#TheMaster|mysql> GRANT REPLICATION SLAVE ON *.*  TO 'doer'@'$newslavehost' IDENTIFIED BY '$slavepass';
command = "GRANT REPLICATION SLAVE ON *.*  TO 'doer'@'{slave_host}' IDENTIFIED BY '{doer_pass}';".format(slave_host=,doer_pass=)
mysql_command(command, host=master)

# Then make sure the slave knows who the master is
#TheNEWSlave|mysql> CHANGE MASTER TO MASTER_HOST='$masterhost', MASTER_USER='doer', MASTER_PASSWORD='$slavepass', MASTER_LOG_FILE='TheMaster-bin.000001', MASTER_LOG_POS=$pos;
command = "CHANGE MASTER TO MASTER_HOST='{master_host}', MASTER_USER='doer', MASTER_PASSWORD='{doer_pass}', MASTER_LOG_FILE='{master_log_file}', MASTER_LOG_POS={master_log_pos};".format(master_host=,doer_pass=,master_log_file=,master_log_pos=)
mysql_command(command, host=slave)

# now its pointing to the master but empty. Do the mysqldump with  --single-transaction so you get a consistent copy, and --master-data so that it picks up the binary log position for you
command = "mysqldump --single-transaction --master-data /tmp/full_sql_dump.sql"
shell_command(command, host=master)
- mysql_db:
    state=dump
    name=all
    target=/tmp/full_sql_dump.sql
    single_transaction=yes

# Copy that dump to slave
#rsync {master_user}@{master_host}:{filename} {slave_user}@{slave_host}:{filename}
command="rsync {filename} {slave_user}@{slave_host}:{filename}".format(master_user=,master_host=,filename=,slave_user=,slave_host=)
shell_command(command, host=master)

#once you import that dump, you should be able to run "show slave status" on the slave and see the correct binary log position.
#mysql < /tmp/full_sql_dump.sql
command = "mysql < /tmp/full_sql_dump.sql"
shell_command(command, host=slave)

command = "rm {filename}".format(filename=)
shell_command(command, host=master)
shell_command(command, host=slave)

# Then just "start slave" and you have replication
# Start the slave
#TheNEWSlave|mysql> START SLAVE;
command = "START SLAVE;"
mysql_command(command, host=slave)

# Then once the slave is healthy:
#mysqlrpladmin --master=user:pass@percona01.nmdev.us --slaves=user:pass@percona03.nmdev.us health
command="mysqlrpladmin --master=user:pass@percona01.nmdev.us --slaves=user:pass@percona03.nmdev.us health"
shell_command(command, host=master)

# Promote it to master
#mysqlrpladmin --master=user:pass@percona01.nmdev.us --slaves=user:pass@percona03.nmdev.us --new-master=user:pass@percona03.nmdev.us --demote-master --rpl-user=user:pass switchover
command="mysqlrpladmin --master=user:pass@percona01.nmdev.us --slaves=user:pass@percona03.nmdev.us --new-master=user:pass@percona03.nmdev.us --demote-master --rpl-user=user:pass switchover"
shell_command(command, host=master)

# Update the DNS and take the master out of rotation
command="STOP SLAVE;"
shell_command(command, host=master)