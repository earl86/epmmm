#!/bin/sh

HOSTNAME=$1

DIR=`dirname $0`

CMD="/usr/bin/python3 $DIR/epmmm_get_memcached_stats.py -n $HOSTNAME"

$CMD 2>&1 > /dev/null
echo 1