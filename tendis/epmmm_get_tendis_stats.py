#!/usr/bin/python

#pip3 install py-zabbix
#pip3 install redis
#pip3 install argparse

import redis
import argparse
from pyzabbix import ZabbixMetric, ZabbixSender

parser = argparse.ArgumentParser(description='Zabbix Tendis status script')
parser.add_argument('-n','--servicename',dest='tendis_servicename',action='store',help='Tendis servicename be the same in zabbix hostname',default=None)
parser.add_argument('-s','--serviceip',dest='tendis_serviceip',action='store',help='Tendis service ip',default=None)
parser.add_argument('-p','--port',dest='tendis_port',action='store',help='Tendis server port',default=8901,type=int)
args = parser.parse_args()

tendis_servicename = args.tendis_servicename
tendis_serviceip = args.tendis_serviceip
tendis_port = args.tendis_port

zabbix_host = '10.17.13.2'      # Zabbix Server IP
zabbix_port = 10051             # Zabbix Server Port


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_host,zabbix_port)
    server.send(packet)


def main():
    client = redis.StrictRedis(host=tendis_serviceip, port=tendis_port)
    server_info = client.info(section='all')

    packet = []
    for item in server_info:
        if (item.startswith('cmdstat_') and item != 'cmdstat_unseen'):
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_calls"),server_info[item]['calls']))
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_usec"),server_info[item]['usec']))
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_usec_per_call"),server_info[item]['usec_per_call']))

        elif (item == 'cmdstat_unseen'):
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_calls"),server_info[item]['calls']))
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_num"),server_info[item]['num']))
        elif (item == 'slave0' or item == 'slave1' or item == 'slave2' or item == 'slave3'):
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_binlog_lag"),server_info[item]['binlog_lag']))
        else:
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % item,server_info[item]))

    #print (packet)
    # Send packet to zabbix
    send_to_zabbix(packet, zabbix_host, zabbix_port)

if __name__ == '__main__':
    main()