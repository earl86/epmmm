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
    args='iostat -y -x -k 2 1'
    
    infolist=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()
    diskinfodict={}
    for info in infolist.split('\n'):
        if (info.startswith('sd') or info.startswith('md') or info.startswith('nvme') ):
            diskinfodict[info.split()[0]] = info.split()[1:]
    
    packet = []
    for disk in diskinfodict:
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.rrqm[%s]" % disk,diskinfodict[disk][0]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.wrqm[%s]" % disk,diskinfodict[disk][1]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.r[%s]" % disk,diskinfodict[disk][2]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.w[%s]" % disk,diskinfodict[disk][3]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.rkB[%s]" % disk,diskinfodict[disk][4]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.wkB[%s]" % disk,diskinfodict[disk][5]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.avgrq-sz[%s]" % disk,diskinfodict[disk][6]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.avgqu-sz[%s]" % disk,diskinfodict[disk][7]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.await[%s]" % disk,diskinfodict[disk][8]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.r_await[%s]" % disk,diskinfodict[disk][9]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.w_await[%s]" % disk,diskinfodict[disk][10]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.svctm[%s]" % disk,diskinfodict[disk][11]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.util[%s]" % disk,diskinfodict[disk][12]))
    
    return packet

def main():
    packet = generate_packet(hostname)
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()
