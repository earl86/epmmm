#!/bin/sh
# The wrapper for zabbix python3 script.
# It runs the script every 30 seconds. and parses the cache file on each following run.
# Test the script using: zabbix_get -s 192.168.1.200 -p 10050 -k "epmmm.mysql.check[your_mysqlservice_hostname,192.168.1.200,3306,check]"
# The script need zabbix_sender and Python Running Environment
# The default monitor mysql port is 3306, if need to monitor other port, you need to add the Macros:{$MYSQL_PORT}=xxxx on the monitor Host
# Remember to change the USERNAME PASSWORD for your's.
# Authors: earl86

USERNAME=zabbix
PASSWORD=zabbix@2014
ZABBIXSERVER=10.17.13.2
ZABBIXSERVER_PORT=10051

HOSTNAME=`hostname`
if [ "${HOSTNAME:0:4}" = "gwon" ]; then
   ZABBIXSERVER=216.66.17.252
fi

SERVICEHOSTNAME=$1
SERVICEIP=$2
SERVICEPORT=$3
ITEM=$4
SERVICEUNIQ=$5

DIR=`dirname $0`

CMD="python3 $DIR/epmmm_get_mysql_stats.py --servicehostname $SERVICEHOSTNAME --serviceip $SERVICEIP --serviceport $SERVICEPORT --username $USERNAME --password $PASSWORD --zabbixserver $ZABBIXSERVER --zabbixserver_port $ZABBIXSERVER_PORT"

if [ "$ITEM" = "mysqld_alive" ]; then
    RES=`HOME=~zabbix mysql -h $SERVICEIP -P $SERVICEPORT -u$USERNAME -p$PASSWORD -N -e 'select 1 from dual;' 2>/dev/null`
    if [ "$RES" = "1" ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ "$ITEM" = "mysqld_cpu_use" ]; then
    if [ -n "$SERVICEUNIQ" ]; then
        pid=`ps -ef |grep -v 'mysqld_safe' |grep "/$SERVICEUNIQ/" |grep -v 'zabbix-agent' |grep -v 'grep' |grep -v ' mysql ' |awk '{print $2}'`
    else
        pid=`sudo -u root /bin/netstat -lntp |grep $SERVICEIP:$SERVICEPORT |grep mysqld |awk '{ print $7}' |awk -F '/' '{ print $1 }'`
    fi
    cpuuse=`top -bn 1 |grep ${pid}|awk '{if ($1=='${pid}') print $9}'`
    echo $cpuuse
    exit
elif [ "$ITEM" = "slave_running" ]; then
    # Check for running slave
    RES=`HOME=~zabbix mysql -h $SERVICEIP -P $SERVICEPORT -u$USERNAME -p$PASSWORD -e 'SHOW SLAVE STATUS\G;' 2>/dev/null | egrep '(Slave_IO_Running|Slave_SQL_Running):' | awk -F: '{print $2}' | tr '\n' ','`
    if [ "$RES" = " Yes, Yes," ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ "$ITEM" = "check" ]; then
    #CMD
    $CMD 2>/dev/null
    echo 1
fi
