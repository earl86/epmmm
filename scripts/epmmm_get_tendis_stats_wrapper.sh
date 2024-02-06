#!/bin/sh
# The wrapper for tendis of zabbix python script.
# It runs the script every 30 seconds. and parses the cache file on each following run.
# Test the script using: zabbix_get -s zabbix_agent_ip -p 10050 -k "epmmm.tendis.check[servicename,serviceip,3901,servicepassword,check]"
# The script need Python Running Environment pip3 install py-zabbix redis argparse
# The default monitor tendis port is 3901, if need to monitor other port, you need to add the Macros:{$TENDIS_PORT}=xxxx and {$TENDIS_PASSWORD}=xxxx on the monitor Host
# Authors: earl86

SERVICEHOSTNAME=$1
SERVICEHOSTIP=$2
SERVICEPORT=$3
ITEM=$4
SERVICEPASSWORD=$5
ZABBIXTYPE=${6:-"co"}


DIR=$(dirname $0)
if [ "${SERVICEPASSWORD}" = "isnull" ]; then
    CMD="/usr/local/bin/python3 $DIR/epmmm_get_tendis_stats.py -n $SERVICEHOSTNAME -s $SERVICEHOSTIP -p $SERVICEPORT -z ${ZABBIXTYPE}"
else
    CMD="/usr/local/bin/python3 $DIR/epmmm_get_tendis_stats.py -n $SERVICEHOSTNAME -s $SERVICEHOSTIP -p $SERVICEPORT -a $SERVICEPASSWORD -z ${ZABBIXTYPE}"
fi

if [ "$ITEM" = "check" ]; then
    $CMD 1>/dev/null 2>/dev/null
    echo 1
fi
