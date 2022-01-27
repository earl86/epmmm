#!/usr/bin/python

import sys
import argparse
import subprocess
from subprocess import Popen
from subprocess import PIPE
from pyzabbix.sender import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
args = parser.parse_args()

hostname = args.hostname
zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)



def generate_packet(hostname):
    args='sar -d -p 3 1'
    
    infolist=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()
    diskinfodict={}
    for info in infolist.split('\n'):
        if (info.startswith('Average')):
            if (info.split()[1].startswith('sd') or info.split()[1].startswith('md') or info.split()[1].startswith('nvme') ):
                diskinfodict[info.split()[1]] = info.split()[2:]
    
    packet = []
    for disk in diskinfodict:
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.tps[%s]" % disk,diskinfodict[disk][0]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.rd_sec[%s]" % disk,diskinfodict[disk][1]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.wr_sec[%s]" % disk,diskinfodict[disk][2]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.avgrq-sz[%s]" % disk,diskinfodict[disk][3]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.avgqu-sz[%s]" % disk,diskinfodict[disk][4]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.await[%s]" % disk,diskinfodict[disk][5]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.svctm[%s]" % disk,diskinfodict[disk][6]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.util[%s]" % disk,diskinfodict[disk][7]))

    return packet

def main():
    packet = generate_packet(hostname)
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()
