#!/usr/bin/python

#pip3 install py-zabbix
#pip3 install redis
#pip3 install argparse

import sys
import redis
import argparse
import os
from configparser import ConfigParser
from pyzabbix import ZabbixMetric, ZabbixSender
import logging

parser = argparse.ArgumentParser(description='Zabbix Tendis status script')
parser.add_argument('-n','--servicename',dest='tendis_servicename',action='store',help='Tendis servicename be the same in zabbix hostname',default=None)
parser.add_argument('-s','--serviceip',dest='tendis_serviceip',action='store',help='Tendis service ip',default=None)
parser.add_argument('-p','--port',dest='tendis_port',action='store',help='Tendis server port',default=3901,type=int)
parser.add_argument('-a','--servicepassword',dest='tendis_password',action='store',help='Tendis service password',default='')
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

tendis_servicename = args.tendis_servicename
tendis_serviceip = args.tendis_serviceip
tendis_port = args.tendis_port
tendis_password = args.tendis_password

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-tendis-stats-%s.log' % (tendis_servicename),
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


def main():
    packet = []
    try:
        if (len(tendis_password) > 0):
            client = redis.Redis(host=tendis_serviceip, port=tendis_port, password=tendis_password, socket_timeout=5, socket_connect_timeout=2)
        else:
            client = redis.Redis(host=tendis_serviceip, port=tendis_port, socket_timeout=5, socket_connect_timeout=2)
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))
        sys.exit()

    try:
        server_info = client.info(section='all')
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))
    else:
        for item in server_info:
            if (item.startswith('cmdstat_') and item != 'cmdstat_unseen'):
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_calls"),server_info[item]['calls']))
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_usec"),server_info[item]['usec']))
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_usec_per_call"),server_info[item]['usec_per_call']))

            elif (item == 'cmdstat_unseen'):
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_calls"),server_info[item]['calls']))
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_num"),server_info[item]['num']))
            elif (item == 'slave0' or item == 'slave1' or item == 'slave2' or item == 'slave3'):
                #slave0:ip=192.168.1.20,port=8901,state=online,offset=84059102,lag=0,binlog_lag=0
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_state"),server_info[item]['state']))
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_lag"),server_info[item]['lag']))
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % (item+"_binlog_lag"),server_info[item]['binlog_lag']))
            elif (item == 'role'):
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % item,server_info[item]))
                if (server_info[item] == 'master'):
                    packet.append(ZabbixMetric(tendis_servicename, "tendis[role_master]", 1))
                else:
                    packet.append(ZabbixMetric(tendis_servicename, "tendis[role_master]", 0))
            elif (item == 'scanner_matrix'):
                itemlist = server_info[item].split(",")
                for i in itemlist:
                    ilist = i.split(" ")
                    packet.append(ZabbixMetric(tendis_servicename, "tendis[%s_%s]" % (item,ilist[0]), ilist[1].replace("ns", "")))
            elif (item == 'deleter_matrix'):
                itemlist = server_info[item].split(",")
                for i in itemlist:
                    ilist = i.split(" ")
                    packet.append(ZabbixMetric(tendis_servicename, "tendis[%s_%s]" % (item,ilist[0]), ilist[1].replace("ns", "")))
            elif (item.startswith('scanpoint')):
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s_%s]" % ('index',item), server_info[item]))
            else:
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % item,server_info[item]))

    try:
        last_slowlog_info = client.slowlog_get(num=1)
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))
    else:
        if last_slowlog_info:
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % 'last_slowlog_id', last_slowlog_info[0]['id']))

    try:
        cluster_info = client.execute_command('cluster info')
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))
    else:
        for key in cluster_info:
            packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % key, cluster_info[key]))

    try:
        rocksdbstats_info_bytes = client.execute_command('info rocksdbstats')
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))
    else:
        rocksdbstats_info = str(rocksdbstats_info_bytes.decode("utf-8")).split("\r\n")
        for line in rocksdbstats_info:
            if (line.find("rocksdb.") == 0):
                line = line.strip()
                line = line.replace(" COUNT ", ".COUNT")
                row = line.split(":")
                packet.append(ZabbixMetric(tendis_servicename, "tendis[%s]" % row[0], row[1]))

    #print(packet)
    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
    except Exception as e:
        logger.error('epmmm %s %s %s, %s!' % (tendis_servicename, tendis_serviceip, tendis_port, e))



if __name__ == '__main__':
    #logger.info('epmmm begin: %s %s %s!' % (tendis_servicename, tendis_serviceip, tendis_port))
    main()
    #logger.info('epmmm begin: %s %s %s!' % (tendis_servicename, tendis_serviceip, tendis_port))
