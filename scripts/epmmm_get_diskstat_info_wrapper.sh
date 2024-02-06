#!/bin/sh

HOSTNAME=$1
ZABBIXTYPE=${2:-"co"}

DIR=$(dirname $0)

CMD="/usr/local/bin/python3 $DIR/epmmm_get_diskstat_info.py -n $HOSTNAME -z ${ZABBIXTYPE}"

$CMD 1>/dev/null 2>/dev/null
echo 1
