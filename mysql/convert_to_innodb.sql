# https://newmediadenver.atlassian.net/wiki/display/DEVOPS/MySQL+MyISAM+to+innoDB+Conversion

# Do this on each node first.
DESYNC_NODE="SET GLOBAL wsrep_OSU_method='RSU';"

# Find all the myisam tables
FIND_ALL_TABLES="SELECT table_schema, TABLE_NAME, table_rows,
CONCAT(ROUND((index_length+data_length)/1024/1024),'MB') AS size 
FROM information_schema.TABLES   
WHERE engine='myisam' AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql');"

# Change a myisam table to InnoDB
CHANGE_TABLE="ALTER TABLE dbname.table_name engine = InnoDB;"


# Do this on each node to finish it off.
SYNC_NODE="SET GLOBAL wsrep_OSU_method='TOI';"

SELECT table_schema, TABLE_NAME, table_rows,
CONCAT(ROUND((index_length+data_length)/1024/1024),'MB') AS size 
FROM information_schema.TABLES   
WHERE engine='myisam' AND table_schema NOT IN ('information_schema', 'performance_schema', 'mysql');