#!/bin/sh
# The wrapper for redis of zabbix python script.
# It runs the script every 30 seconds. and parses the cache file on each following run.
# Test the script using: zabbix_get -s servicename -p 10050 -k "epmmm.redis.check[servicename,serviceip,6379,check]"
# The script need Python Running Environment pip3 install py-zabbix redis argparse
# The default monitor redis port is 6379, if need to monitor other port, you need to add the Macros:{$REDIS_PORT}=xxxx on the monitor Host
# Remember to change the REDIS PASSWORD for your's.
# Authors: earl86

SERVICEHOSTNAME=$1
SERVICEHOSTIP=$2
SERVICEPORT=$3
ITEM=$4
PASSWORD=$5
ZABBIXTYPE=${6:-"co"}


DIR=$(dirname $0)

if [ "$PASSWORD" = "isnull" ]; then
    CMD="/usr/local/bin/python3 $DIR/epmmm_get_redis_stats.py -n $SERVICEHOSTNAME -s $SERVICEHOSTIP -p $SERVICEPORT -z ${ZABBIXTYPE}"
else
    CMD="/usr/local/bin/python3 $DIR/epmmm_get_redis_stats.py -n $SERVICEHOSTNAME -s $SERVICEHOSTIP -p $SERVICEPORT -a $PASSWORD -z ${ZABBIXTYPE}"
fi

if [ "$ITEM" = "check" ]; then
    $CMD 1>/dev/null 2>/dev/null
    echo 1
fi
