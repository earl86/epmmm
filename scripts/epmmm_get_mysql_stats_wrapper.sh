#!/bin/sh
# The wrapper for zabbix python3 script.
# It runs the script every 30 seconds. and parses the cache file on each following run.
# Test the script using: zabbix_get -s 192.168.1.200 -p 10050 -k "epmmm.mysql.check[your_mysqlservice_name,192.168.1.200,3306,check,SERVICEUNIQ,co]"
# The script need zabbix_sender and Python Running Environment
# The default monitor mysql port is 3306, if need to monitor other port, you need to add the Macros:{$MYSQL_PORT}=xxxx on the monitor Host
# Remember to change the USERNAME PASSWORD for your's.
# Authors: wangchao

USERNAME=zabbix
PASSWORD=zabbix@2014

SERVICENAME=$1
SERVICEIP=$2
SERVICEPORT=$3
ITEM=$4
SERVICEUNIQ=$5
ZABBIXTYPE=${6:-"co"}

HOSTNAME=${HOSTNAME%%.*}

if [ "${ZABBIXTYPE}" = "google" ]; then
    SERVICEIP=`grep bind_address /etc/my-${SERVICEUNIQ}.cnf |awk -F '=' '{print $2}' |sed 's/ //g'`
fi

DIR=$(dirname $0)

CMD="/usr/local/bin/python3 $DIR/epmmm_get_mysql_stats.py --servicename ${SERVICENAME} --serviceip ${SERVICEIP} --serviceport ${SERVICEPORT} --username ${USERNAME} --password ${PASSWORD} --zabbix_type ${ZABBIXTYPE}"

if [ "${ITEM}" = "mysqld_cpu_use" ]; then
    if [ -n "${SERVICEUNIQ}" ]; then
        pid=`ps -ef |grep 'mysqld ' |grep -v 'mysqld_safe' |grep "/${SERVICEUNIQ}/" |grep -v ' rsync ' |grep -v 'zabbix-agent' |grep -v 'grep' |grep -v ' mysql ' |awk '{print $2}'`
    else
        pid=`sudo -u root /bin/netstat -lntp |grep ${SERVICEIP}:${SERVICEPORT} |grep mysqld |awk '{ print $7}' |awk -F '/' '{ print $1 }'`
    fi
    cpuuse=`top -bn 1 |grep ${pid}|awk '{if ($1=='${pid}') print $9}'`
    echo $cpuuse
elif [ "${ITEM}" = "check" ]; then
    $CMD 1>/dev/null 2>/dev/null
    echo 1
fi
