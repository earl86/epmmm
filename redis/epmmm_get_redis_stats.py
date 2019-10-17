#!/usr/bin/python

import sys
import redis
import argparse
from pyzabbix import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='Zabbix Redis status script')
parser.add_argument('-s','--servicename',dest='redis_servicename',action='store',help='Redis servicename be the same in zabbix hostname',default=None)
parser.add_argument('-p','--port',dest='redis_port',action='store',help='Redis server port',default=6379,type=int)
parser.add_argument('-a','--auth',dest='redis_pass',action='store',help='Redis server pass',default=None)
args = parser.parse_args()

redis_servicename = args.redis_servicename
redis_port = args.redis_port
redis_pass = args.redis_pass

zabbix_host = '192.168.0.1'      # Your Zabbix Server IP
zabbix_port = 10051              # Your Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)


def main():

    client = redis.StrictRedis(host=redis_servicename, port=redis_port, password=redis_pass)
    server_info = client.info()

    packet = []
    for item in server_info:
        packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item,server_info[item]))
    #print (packet)
    # Send packet to zabbix
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()