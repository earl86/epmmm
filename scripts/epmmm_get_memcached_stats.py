#!/usr/bin/env python3
#coding=utf-8
#encoding:utf8
#pip3 install argparse
#pip3 install pymemcache
#pip3 install py-zabbix

import argparse
import logging
import os
import sys
from configparser import ConfigParser
from pyzabbix.sender import ZabbixMetric, ZabbixSender
from pymemcache.client.base import Client


parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None, required=True)
parser.add_argument('-l','--memcached_ip',dest='memcached_ip',action='store',help='memcached_ip',default='127.0.0.1')
parser.add_argument('-p','--memcached_port',dest='memcached_port',action='store',type=int,help='memcached_port',default=11211)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

HOSTNAME = args.hostname
MEMCACHED_IP = args.memcached_ip
MEMCACHED_PORT = args.memcached_port


logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-memcached-stats-%s.log' % (HOSTNAME),
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')

logger = logging.getLogger(__name__)


basedir, _ = os.path.split(os.path.abspath(sys.argv[0]))
cfg = ConfigParser()
if os.path.exists('{}/zabbix_meta.ini'.format(basedir)):
    cfg.read('{}/zabbix_meta.ini'.format(basedir))
else:
    print('zabbix_meta.ini 元数据配置文件不存在')
    logger.error('zabbix_meta.ini 元数据配置文件不存在')
    sys.exit()
META_ZABBIX_SERVER_IP = cfg.get(args.zabbix_type,'META_ZABBIX_SERVER_IP')
META_ZABBIX_SERVER_PORT = cfg.getint(args.zabbix_type,'META_ZABBIX_SERVER_PORT')


def generate_packet(hostname):
    packet = []
    try:
        client = Client((MEMCACHED_IP, MEMCACHED_PORT))
        memstatsdict = client.stats()

        for memstats in memstatsdict:
            #print(memstats)
            #print(memstatsdict[memstats])
            packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % memstats.decode(),memstatsdict[memstats]))
        if b'replication' in memstatsdict:
            role_info = memstatsdict[b'replication'].decode()
            if (role_info == "MASTER"):
                packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'master', 1))
            else:
                #SLAVE,RELAY
                packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'master', 0))
        else:
            packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'master', 1))
        packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'status', 1))
    except Exception as e:
        logger.info('epmmm %s, %s, %s!', hostname, MEMCACHED_IP, e)
        packet.append(ZabbixMetric(hostname, "memcached_stats[%s]" % 'status', 0))

    #print(packet)
    return packet



def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_server=zabbix_host, zabbix_port=zabbix_port, chunk_size=100, timeout=10)
    server.send(packet)

def main():
    packet = generate_packet(HOSTNAME)
    #print(packet)
    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
    except Exception as e:
        logger.error('epmmm: %s %s %s. %s!' % ( HOSTNAME, MEMCACHED_IP, MEMCACHED_PORT, e))

if __name__ == '__main__':
    main()
