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
ZABBIXSERVER=192.168.0.1

SERVICEHOSTNAME=$1
SERVICEHOST=$2
SERVICEPORT=$3
ITEM=$4

DIR=`dirname $0`

CMD="/usr/bin/python $DIR/epmmm_get_mysql_stats.py --servicehostname $SERVICEHOSTNAME --servicehost $SERVICEHOST --serviceport $SERVICEPORT --username $USERNAME --password $PASSWORD"
CACHEFILE="/tmp/$SERVICEHOST-$SERVICEPORT-epmmm-mysql_zabbix_stats.txt"

if [ "$ITEM" = "mysqld_alive" ]; then
    RES=`HOME=~zabbix mysql -h $SERVICEHOST -P $SERVICEPORT -u$USERNAME -p$PASSWORD -N -e 'select 1 from dual;' 2>/dev/null`
    if [ "$RES" = "1" ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ "$ITEM" = "slave_running" ]; then
    # Check for running slave
    RES=`HOME=~zabbix mysql -h $SERVICEHOST -P $SERVICEPORT -u$USERNAME -p$PASSWORD -e 'SHOW SLAVE STATUS\G' 2>/dev/null | egrep '(Slave_IO_Running|Slave_SQL_Running):' | awk -F: '{print $2}' | tr '\n' ','`
    if [ "$RES" = " Yes, Yes," ]; then
        echo 1
    else
        echo 0
    fi
    exit
elif [ -e $CACHEFILE ]; then
    # Check and run the script
    #TIMEFLM=`stat -c %Y /tmp/$SERVICEHOST-$SERVICEPORT-epmmm-mysql_zabbix_stats.txt`
    echo 1
    TIMEFLM=`stat -c %Y $CACHEFILE`
    TIMENOW=`date +%s`
    if [ `expr $TIMENOW - $TIMEFLM` -gt 30 ]; then
        rm -f $CACHEFILE
        $CMD 2>&1 > /dev/null
    fi
else
    echo 1
    $CMD 2>&1 > /dev/null
fi

# Parse cache file
if [ -e $CACHEFILE ]; then
    zabbix_sender -z $ZABBIXSERVER -p 10051 -i $CACHEFILE 2>&1 > /dev/null 
else
    echo "ERROR: run the command manually to investigate the problem: $CMD"
fi


