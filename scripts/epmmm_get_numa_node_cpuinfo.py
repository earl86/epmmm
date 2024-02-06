#!/usr/bin/env python
#pip3 install strip_ansi
#pip3 install pexpect

import re
import logging
import time
import pexpect
import argparse
import os
import sys
from configparser import ConfigParser
from strip_ansi import strip_ansi
from pyzabbix.sender import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

hostname = args.hostname

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-numa-node-cpuinfo.log',
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

def generate_packet(hostname):
    packet = []
    cmd = 'top -n 2 -d 10'
    child = pexpect.spawn(cmd, timeout=10, encoding='utf-8',env = {"TERM": "dumb"})
    child.send('2')
    time.sleep(1)
    info=child.read()
    #logger.info('%s!', info)
    child.close()
    a=info.split('\n')
    for line in a:
        if (line.find("%Node") == 0):
            newline =  re.split(r':|,', strip_ansi(line))
            #logger.info('%s!', newline)
            cpunode=newline[0].strip().strip('%')
            packet.append(ZabbixMetric(hostname, "cpu.numa.us.[%s]" % cpunode,newline[1].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.sy.[%s]" % cpunode,newline[2].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.ni.[%s]" % cpunode,newline[3].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.id.[%s]" % cpunode,newline[4].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.wa.[%s]" % cpunode,newline[5].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.hi.[%s]" % cpunode,newline[6].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.si.[%s]" % cpunode,newline[7].strip().split()[0]))
            packet.append(ZabbixMetric(hostname, "cpu.numa.st.[%s]" % cpunode,newline[8].strip().split()[0]))
    #logger.info('%s!', packet)
    return packet

def main():
    try:
        packet = generate_packet(hostname)
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
        print("1")
    except Exception as e:
        logger.error('epmmm: %s. %s!' % ( hostname, e))
        print("0")


if __name__ == '__main__':
    main()
