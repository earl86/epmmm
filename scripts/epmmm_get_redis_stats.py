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

parser = argparse.ArgumentParser(description='Zabbix Redis status script')
parser.add_argument('-n','--servicename',dest='redis_servicename',action='store',help='Redis servicename be the same in zabbix hostname',default=None)
parser.add_argument('-s','--serviceip',dest='redis_serviceip',action='store',help='Redis service ip',default=None)
parser.add_argument('-p','--port',dest='redis_port',action='store',help='Redis server port',default=6379,type=int)
parser.add_argument('-a','--auth',dest='redis_pass',action='store',help='Redis server pass',default=None, required=False)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

redis_servicename = args.redis_servicename
redis_serviceip = args.redis_serviceip
redis_port = args.redis_port
redis_pass = args.redis_pass

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-redis-stats.log-%s' % (redis_servicename),
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
    client = redis.StrictRedis(host=redis_serviceip, port=redis_port, password=redis_pass)
    server_info = client.info(section='all')

    for item in server_info:
        if (item == 'mem_fragmentation_bytes'):
            if (int(server_info[item]) < 0):
                server_info[item] = 0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
        elif (item == 'rdb_current_bgsave_time_sec'):
            if (int(server_info[item]) < 0):
                server_info[item] = 0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
        elif (item == 'aof_last_rewrite_time_sec'):
            if (int(server_info[item]) < 0):
                server_info[item] = 0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
        elif (item == 'aof_current_rewrite_time_sec'):
            if (int(server_info[item]) < 0):
                server_info[item] = 0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
        elif (item == 'second_repl_offset'):
            if (int(server_info[item]) < 0):
                server_info[item] = 0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
        elif (item.startswith('cmdstat_') and item != 'cmdstat_unseen'):
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_calls"), server_info[item]['calls']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_usec"), server_info[item]['usec']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_usec_per_call"), server_info[item]['usec_per_call']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_rejected_calls"), server_info[item]['rejected_calls']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_failed_calls"), server_info[item]['failed_calls']))
        elif (item == 'cmdstat_unseen'):
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_calls"), server_info[item]['calls']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_num"), server_info[item]['num']))
        elif (item == 'slave0' or item == 'slave1' or item == 'slave2' or item == 'slave3'):
            #slave0:ip=10.18.2.7,port=6380,state=online,offset=29763708543,lag=0
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_state"), server_info[item]['state']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_offset"), server_info[item]['offset']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_lag"), server_info[item]['lag']))
        elif (item == 'role'):
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
            if (server_info[item] == 'master'):
                packet.append(ZabbixMetric(redis_servicename, "redis[role_master]", 1))
            else:
                packet.append(ZabbixMetric(redis_servicename, "redis[role_master]", 0))
        elif (item.startswith('errorstat_')):
            #errorstat_ERR:count=1
            #errorstat_MOVED:count=1
            #errorstat_NOAUTH:count=1
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_count"), server_info[item].split('=')[1]))
        elif (item.startswith('db')):
            #db0:keys=3919,expires=3811,avg_ttl=1270019721
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_keys"), server_info[item]['keys']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_expires"), server_info[item]['expires']))
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % (item+"_avg_ttl"), server_info[item]['avg_ttl']))
        else:
            packet.append(ZabbixMetric(redis_servicename, "redis[%s]" % item, server_info[item]))
    #print(packet)
    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
    except Exception as e:
        logger.error('epmmm: %s %s %s. %s!' % ( redis_servicename, redis_serviceip, redis_port, e))



if __name__ == '__main__':
    main()
