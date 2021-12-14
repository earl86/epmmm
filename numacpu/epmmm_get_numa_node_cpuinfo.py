#!/usr/bin/env python
#pip3 install strip_ansi
#pip3 install pexpect

import pexpect
import argparse
from strip_ansi import strip_ansi
from pyzabbix.sender import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n','--hostname',dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
args = parser.parse_args()

hostname = args.hostname
zabbix_host = '192.168.1.100'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)

def generate_packet(hostname):
    cmd = 'top -n 2'
    child = pexpect.spawn(cmd, timeout=2, encoding='utf-8',env = {"TERM": "dumb"})
    child.send('2')
    info=child.read()
    a=info.split('\n')
    packet = []
    for line in a:
        if (line.find("%Node") == 0):
            #print(strip_ansi(line))
            newline=strip_ansi(line).split()
            cpunude=strip_ansi(newline[0]).strip('%')
            packet.append(ZabbixMetric(hostname, "cpu.numa.us.[%s]" % cpunude,strip_ansi(newline[2])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.sy.[%s]" % cpunude,strip_ansi(newline[4])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.ni.[%s]" % cpunude,strip_ansi(newline[6])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.id.[%s]" % cpunude,strip_ansi(newline[8])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.wa.[%s]" % cpunude,strip_ansi(newline[10])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.hi.[%s]" % cpunude,strip_ansi(newline[12])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.si.[%s]" % cpunude,strip_ansi(newline[14])))
            packet.append(ZabbixMetric(hostname, "cpu.numa.st.[%s]" % cpunude,strip_ansi(newline[16])))

    return packet

def main():
    packet = generate_packet(hostname)
    #print(packet)
    send_to_zabbix(packet, zabbix_host, zabbix_port)
    print("1")

if __name__ == '__main__':
    main()
