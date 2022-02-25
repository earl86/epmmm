#!/usr/bin/env python
#pip3 install strip_ansi
#pip3 install pexpect

import re
import logging
import time
import pexpect
import argparse
from strip_ansi import strip_ansi
from pyzabbix.sender import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
args = parser.parse_args()

hostname = args.hostname
zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-numa-node-cpuinfo.log',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')

logger = logging.getLogger(__name__)

def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
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
    packet = generate_packet(hostname)
    #print(packet)
    send_to_zabbix(packet, zabbix_host, zabbix_port)
    print("1")

if __name__ == '__main__':
    main()
