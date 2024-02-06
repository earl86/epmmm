#!/bin/sh

HOSTNAME=$1
SERVICEIP=$2
SERVICEPORT=$3
ZABBIXTYPE=${4:-"co"}

DIR=$(dirname $0)

CMD="/usr/local/bin/python3 $DIR/epmmm_get_memcached_stats.py -n $HOSTNAME -l $SERVICEIP -p $SERVICEPORT -z ${ZABBIXTYPE}"

$CMD 1>/dev/null 2>/dev/null
echo 1
