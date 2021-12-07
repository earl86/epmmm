#!/usr/bin/python

import sys
import argparse
from pyzabbix.sender import ZabbixMetric, ZabbixSender
import subprocess
from subprocess import Popen
from subprocess import PIPE

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
args = parser.parse_args()

hostname = args.hostname
zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
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

    return packet

def main():
    packet = get_socket_stats(hostname)
    #print(packet)
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()
