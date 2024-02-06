#!/usr/bin/python

import sys
import argparse
import os
from configparser import ConfigParser
from pyzabbix.sender import ZabbixMetric, ZabbixSender
import subprocess
from subprocess import Popen
from subprocess import PIPE
import logging

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

hostname = args.hostname



logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-net-stats.log',
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


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_server=zabbix_host, zabbix_port=zabbix_port, chunk_size=100, timeout=10)
    server.send(packet)

def get_socket_stats(hostname):
    packet = []
    procfile = open("/proc/net/sockstat", "r").readlines()
    for info in procfile:
        infolist=info.split()
        if(infolist[0] == 'sockets:'):
            packet.append(ZabbixMetric(hostname, "sockstat.sockets",infolist[2]))
        elif(infolist[0] == 'TCP:'):
            packet.append(ZabbixMetric(hostname, "sockstat.tcp.inuse",infolist[2]))
            packet.append(ZabbixMetric(hostname, "sockstat.tcp.orphan",infolist[4]))
            packet.append(ZabbixMetric(hostname, "sockstat.tcp.timewait",infolist[6]))
            packet.append(ZabbixMetric(hostname, "sockstat.tcp.allocated",infolist[8]))
            packet.append(ZabbixMetric(hostname, "sockstat.tcp.mem",int(infolist[10])*4096))
        elif(infolist[0] == 'UDP:'):
            packet.append(ZabbixMetric(hostname, "sockstat.udp.inuse",infolist[2]))
            packet.append(ZabbixMetric(hostname, "sockstat.udp.mem",int(infolist[4])*4096))
        elif(infolist[0] == 'UDPLITE:'):
            packet.append(ZabbixMetric(hostname, "sockstat.udplite.inuse",infolist[2]))
        elif(infolist[0] == 'RAW:'):
            packet.append(ZabbixMetric(hostname, "sockstat.raw.inuse",infolist[2]))
        elif(infolist[0] == 'FRAG:'):
            packet.append(ZabbixMetric(hostname, "sockstat.frag.inuse",infolist[2]))
            packet.append(ZabbixMetric(hostname, "sockstat.frag.mem",int(infolist[4])*4096))

    args="ss -an |grep tcp| awk '{++S[$2]} END {for(a in S) print a\":\"S[a]}'"

    infostr=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()
    for info in infostr.split():
        infolist=info.split(':')
        packet.append(ZabbixMetric(hostname, "sockstat.%s.number" % infolist[0],infolist[1]))

    cmd = "ss -s | head -2 | awk '{print $2}'"
    dataStr=Popen(args=cmd, stdout=PIPE, shell=True).stdout.read().decode()
    data = dataStr.split("\n")
    packet.append(ZabbixMetric(hostname, "sockstat.Total.number",data[0]))
    packet.append(ZabbixMetric(hostname, "sockstat.TCP.number",data[1]))

    return packet

def main():
    packet = get_socket_stats(hostname)
    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
    except Exception as e:
        logger.error('epmmm: %s. %s!' % ( hostname, e))

if __name__ == '__main__':
    main()
