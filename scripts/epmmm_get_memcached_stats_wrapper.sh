#!/bin/sh

# Test the script using: zabbix_get -s zabbix_agent_ip -p 10050 -k "get_memcached_stats[{HOST.NAME},{HOST.IP},{$MEMCACHED_PORT},{$ZABBIXTYPE},check,{$SERVICEUNIQ}]"
# Test the script using: zabbix_get -s zabbix_agent_ip -p 10050 -k "get_memcached_stats[{HOST.NAME},{HOST.IP},{$MEMCACHED_PORT},{$ZABBIXTYPE},memcached_cpu_use,{$SERVICEUNIQ}]"


HOSTNAME=$1
MEMCACHED_IP=$2
MEMCACHED_PORT=$3
ZABBIXTYPE=${4:-"co"}
ITEM=$5
SERVICEUNIQ=$6

DIR=$(dirname $0)

CMD="/usr/local/bin/python3 $DIR/epmmm_get_memcached_stats.py -n ${HOSTNAME} -l ${MEMCACHED_IP} -p ${MEMCACHED_PORT} -z ${ZABBIXTYPE}"


if [ "${ITEM}" = "memcached_cpu_use" ]; then
    if [ -n "${SERVICEUNIQ}" ]; then
        pid=`ps -ef |grep memcached|grep -v 'grep'|grep -v 'zabbix-agent'|grep "${SERVICEUNIQ}"|awk '{print $2}'`
        cpuuse=`top -b -p ${pid} -n 1 |grep ${pid}|tail -n 1|awk '{print $9}'`
        echo $cpuuse
    fi
elif [ "$ITEM" = "check" ]; then
    $CMD 1>/dev/null 2>/dev/null
    echo 1
fi
