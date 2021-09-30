#!/usr/bin/python

#pip3 install py-zabbix
#pip3 install redis
#pip3 install argparse
import sys
import redis
import argparse
from pyzabbix import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='Zabbix Redis status script')
parser.add_argument('-n','--servicename',dest='redis_servicename',action='store',help='Redis servicename be the same in zabbix hostname',default=None)
parser.add_argument('-s','--serviceip',dest='redis_serviceip',action='store',help='Redis service ip',default=None)
parser.add_argument('-p','--port',dest='redis_port',action='store',help='Redis server port',default=6379,type=int)
parser.add_argument('-a','--auth',dest='redis_pass',action='store',help='Redis server pass',default=None, required=False)
args = parser.parse_args()

redis_servicename = args.redis_servicename
redis_serviceip = args.redis_serviceip
redis_port = args.redis_port
redis_pass = args.redis_pass

zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)


def main():

    client = redis.StrictRedis(host=redis_serviceip, port=redis_port, password=redis_pass)
    server_info = client.info()

    packet = []
    for item in server_info:
        packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item,server_info[item]))
    #print (packet)
    # Send packet to zabbix
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()