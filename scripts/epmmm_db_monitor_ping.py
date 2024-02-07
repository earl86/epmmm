#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import re
import subprocess
import argparse
import os
from configparser import ConfigParser
from pyzabbix.sender import ZabbixMetric, ZabbixSender

from epmmm_db_monitor_ping_discover import get_servicename

from log import HandleLog
logger = HandleLog("epmmm-db-monitor-ping-stats.log").getMyLogger()

from alarm import send_message_to_skypealarm


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--hostname', dest='hostname', action="store", help="input the hostname", required=True)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()


HOSTNAME=args.hostname

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


DBAContacts="wangchao wanjianjun wangbaoxin lizhe wangdeyu chenjun"


def send_to_zabbix(packet, zabbix_host, zabbix_port):
    try:
        server = ZabbixSender(zabbix_server=zabbix_host, zabbix_port=zabbix_port, chunk_size=100, timeout=10)
        server.send(packet)
    except Exception as e:
        logger.error('{}'.format(e))


class forMap:
    def __init__(self):
        self.name = '没啥用的初始化'

    def run(self, servicename, hostname, network_type):
        packet = []
        try:
            if network_type == 0:
                cmd = '/usr/sbin/fping -c 5 -p 500 -t 500 -q -u {}'.format(servicename)
            elif network_type == 1:
                cmd = '/usr/sbin/fping -c 5 -p 1000 -t 1000 -q -u {}'.format(servicename)
            else:
                cmd = '/usr/sbin/fping -c 5 -p 1000 -t 1000 -q -u {}'.format(servicename)

            res = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE).stderr.read().decode()
            if res:
                packet_loss = int(re.search(r'loss = \d+/\d+/(\d+)%', str(res)).group(1))
                if packet_loss != 100:
                    ping_response_min = re.search(r'max = ([\d|.]{1,})/([\d|.]{1,})/([\d|.]{1,})', res).group(1)
                    ping_response_avg = re.search(r'max = ([\d|.]{1,})/([\d|.]{1,})/([\d|.]{1,})', res).group(2)
                    ping_response_max = re.search(r'max = ([\d|.]{1,})/([\d|.]{1,})/([\d|.]{1,})', res).group(3)
                    if packet_loss > 0:
                        logger.error("fping: %s .results: %s" %(cmd, res))
                        logger.error("fping loss %s : response: min %s avg %s max %s" %(packet_loss, ping_response_min, ping_response_avg, ping_response_max))
                        try:
                            message = "db-monitor: %s ping %s : loss %s ,ping_response min,avg,max: %s, %s, %s .\n CMD: %s \n pls call %s " % (hostname, servicename, packet_loss, ping_response_min, ping_response_avg, ping_response_max, cmd, DBAContacts)
                            alarm_level = "INFO"
                            send_message_to_skypealarm(message, alarm_level)
                        except Exception as e:
                            logger.error('{}'.format(e))
                else:
                    ping_response_min = 100.0
                    ping_response_avg = 100.0
                    ping_response_max = 100.0
                    logger.error("fping loss %s, cmd: %s results: %s" % (packet_loss, cmd, res))
                    try:
                        message = "db-monitor: %s ping %s : loss %s . CMD: %s \n pls call %s " % (hostname, servicename, packet_loss, cmd, DBAContacts)
                        alarm_level = "CRITICAL"
                        send_message_to_skypealarm(message, alarm_level)
                    except Exception as e:
                        logger.error('{}'.format(e))

                packet.append(ZabbixMetric(hostname, "db_monitor.ping_loss[{}]".format(servicename), packet_loss))
                packet.append(ZabbixMetric(hostname, "db_monitor.ping_response_min[{}]".format(servicename), ping_response_min))
                packet.append(ZabbixMetric(hostname, "db_monitor.ping_response_avg[{}]".format(servicename), ping_response_avg))
                packet.append(ZabbixMetric(hostname, "db_monitor.ping_response_max[{}]".format(servicename), ping_response_max))
                return packet
            else:
                logger.error('db-monitor: exec fping error')
                return None
        except Exception as e:
            logger.error('{}'.format(e))


def main():
    servicename = get_servicename(HOSTNAME)[0]
    network_type = get_servicename(HOSTNAME)[1]
    if servicename:
        tt = forMap()
        packet = tt.run(servicename, HOSTNAME, network_type)
        #print(packet)
        if packet:
            send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
        else:
            logger.error('db-monitor: packet %s' %(packet))


if __name__ == '__main__':
    main()
