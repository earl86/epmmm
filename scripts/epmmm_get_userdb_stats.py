#!/usr/bin/python

import sys
import subprocess
import os
from configparser import ConfigParser
from subprocess import Popen
from subprocess import PIPE
import argparse
from pyzabbix import ZabbixMetric, ZabbixSender
import logging

parser = argparse.ArgumentParser(description='Zabbix userdb status script')
parser.add_argument('-n','--servicename',dest='userdb_servicename',action='store',help='userdb servicename be the same in zabbix hostname',default=None)
parser.add_argument('-s','--serviceip',dest='userdb_serviceip',action='store',help='userdb service ip',default=None)
parser.add_argument('-p','--port',dest='userdb_port',action='store',help='userdb server port',default=6379,type=int)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

userdb_servicename = args.userdb_servicename
userdb_serviceip = args.userdb_serviceip
userdb_port = args.userdb_port

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-userdb-stats-%s.log' % (userdb_servicename),
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


def generate_packet():
    args="userdb_tools -i %s -p %d stats|grep command_total" % (userdb_serviceip, userdb_port)
    packet = []
    lines=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()
    linelist=lines.strip().split(' ')

    for vline in linelist[2:]:
        key=vline[:-1].split('[')
        packet.append(ZabbixMetric(userdb_servicename, "userdb_stats[%s]" % key[0],key[1]))

    if len(packet):
        packet.append(ZabbixMetric(userdb_servicename, "userdb_stats[%s]" % 'userdb_alived',1))
    else:
        packet.append(ZabbixMetric(userdb_servicename, "userdb_stats[%s]" % 'userdb_alived',0))

    return packet

def main():
    packet = generate_packet()
    #print(packet)
    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
    except Exception as e:
        logger.error('epmmm: %s %s %s. %s!' % ( userdb_servicename, userdb_serviceip, userdb_port, e))


if __name__ == '__main__':
    main()
