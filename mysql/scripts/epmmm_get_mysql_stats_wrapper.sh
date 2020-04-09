#!/bin/sh
# The wrapper for zabbix python script.
# It runs the script every 30 seconds. and parses the cache file on each following run.
# Test the script using: zabbix_get -s 10.148.0.3 -p 10050 -k "epmmm.mysql.check[zabbixmysql,10.148.0.3,3306,check]"
# The script need zabbix_sender and Python Running Environment
# The default monitor mysql port is 3306, if need to monitor other port, you need to add the Macros:{$MYSQL_PORT}=xxxx on the monitor Host
# Remember to change the USERNAME PASSWORD ZABBIXSERVER for your's.
# Authors: earl86

USERNAME=zabbix
PASSWORD=zabbix
ZABBIXSERVER=192.168.1.2
ZABBIXSERVER_PORT=10051

HOSTNAME=`hostname`
if [ "${HOSTNAME:0:4}" = "xxx" ]; then
   ZABBIXSERVER=192.168.1.3
fi

SERVICEHOSTNAME=$1
SERVICEIP=$2
SERVICEPORT=$3
ITEM=$4

DIR=`dirname $0`

CMD="/usr/bin/python $DIR/epmmm_get_mysql_stats.py --servicehostname $SERVICEHOSTNAME --serviceip $SERVICEIP --serviceport $SERVICEPORT --username $USERNAME --password $PASSWORD --zabbixserver $ZABBIXSERVER --zabbixserver_port $ZABBIXSERVER_PORT"

if [ "$ITEM" = "mysqld_alive" ]; then
    RES=`HOME=~zabbix mysql -h $SERVICEIP -P $SERVICEPORT -u$USERNAME -p$PASSWORD -N -e 'select 1 from dual;' 2>/dev/null`
    if [ "$RES" = "1" ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ "$ITEM" = "slave_running" ]; then
    # Check for running slave
    RES=`HOME=~zabbix mysql -h $SERVICEIP -P $SERVICEPORT -u$USERNAME -p$PASSWORD -e 'SHOW SLAVE STATUS\G' 2>/dev/null | egrep '(Slave_IO_Running|Slave_SQL_Running):' | awk -F: '{print $2}' | tr '\n' ','`
    if [ "$RES" = " Yes, Yes," ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ "$ITEM" = "check" ]; then
    $CMD
    if [ $? = "0" ]; then
    	echo 1
    else
    	echo 0
    fi
fi


