#!/bin/sh

HOSTNAME=$1

DIR=`dirname $0`

CMD="python3 $DIR/epmmm_get_iostat_info.py -n $HOSTNAME"

$CMD 2>&1 > /dev/null
echo 1