#!/usr/bin/env python3
#coding=utf-8
#encoding:utf8
#pip3 install argparse
#pip3 install pymemcache
#pip3 install py-zabbix

import argparse
from pyzabbix.sender import ZabbixMetric, ZabbixSender
from pymemcache.client.base import Client


parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None, required=True)
parser.add_argument('-l','--serviceip',dest='serviceip',action='store',help='serviceip for memcached',default='127.0.0.1')
parser.add_argument('-p','--serviceport',dest='serviceport',action='store',type=int,help='serviceport for memcached',default=11211)
args = parser.parse_args()

hostname = args.hostname
serviceip = args.serviceip
serviceport = args.serviceport

zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def generate_packet(hostname):
    packet = []
    try:
        client = Client((serviceip, serviceport))
        memstatsdict = client.stats()
    
        for memstats in memstatsdict:
            #print(memstats)
            #print(memstatsdict[memstats])
            packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % memstats.decode(),memstatsdict[memstats]))
        packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'status',1))
    except Exception as e:
        print(e)
        packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'status',0))

    #print(packet)    
    return packet



def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)

def main():
    packet = generate_packet(hostname)
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()
