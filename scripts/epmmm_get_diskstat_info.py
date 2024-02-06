#!/usr/bin/python

#pip3 install argparse
#pip3 install py-zabbix

import sys
import argparse
import subprocess
import os
from configparser import ConfigParser
from multiprocessing import Process, Manager
from subprocess import Popen
from subprocess import PIPE
from pyzabbix.sender import ZabbixMetric, ZabbixSender
import logging

parser = argparse.ArgumentParser(description='host name')
parser.add_argument('-n', '--hostname', dest='hostname',action='store',help='hostname in zabbix hostname',default=None)
parser.add_argument('-z', '--zabbix_type', dest='zabbix_type', action="store", help="zabbix_type", default='co')
args = parser.parse_args()

hostname = args.hostname

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-diskstat-stats.log',
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


packet = Manager().list()

def send_to_zabbix(packet, zabbix_host, zabbix_port):
    server = ZabbixSender(zabbix_server=zabbix_host, zabbix_port=zabbix_port, chunk_size=100, timeout=10)
    server.send(packet)


def generate_sar_packet(hostname):
    global packet
    diskinfodict={}

    args='sar -d -p 2 1'
    infolist=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()

    for info in infolist.split('\n'):
        if (info.startswith('Average')):
            if (info.split()[1].startswith('sd') or info.split()[1].startswith('md') or info.split()[1].startswith('nvme') ):
                diskinfodict[info.split()[1]] = info.split()[2:]

    for disk in diskinfodict:
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.tps[%s]" % disk, diskinfodict[disk][0]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.rd_sec[%s]" % disk, diskinfodict[disk][1]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.wr_sec[%s]" % disk, diskinfodict[disk][2]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.avgrq-sz[%s]" % disk, diskinfodict[disk][3]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.avgqu-sz[%s]" % disk, diskinfodict[disk][4]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.await[%s]" % disk, diskinfodict[disk][5]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.svctm[%s]" % disk, diskinfodict[disk][6]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.sar-d-p.util[%s]" % disk, diskinfodict[disk][7]))


def generate_iostat_packet(hostname):
    global packet
    diskinfodict={}

    args='iostat -y -x -k 2 1'
    infolist=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()

    for info in infolist.split('\n'):
        if (info.startswith('sd') or info.startswith('md') or info.startswith('nvme') ):
            diskinfodict[info.split()[0]] = info.split()[1:]

    for disk in diskinfodict:
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.rrqm[%s]" % disk, diskinfodict[disk][0]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.wrqm[%s]" % disk, diskinfodict[disk][1]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.r[%s]" % disk, diskinfodict[disk][2]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.w[%s]" % disk, diskinfodict[disk][3]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.rkB[%s]" % disk, diskinfodict[disk][4]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.wkB[%s]" % disk, diskinfodict[disk][5]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.avgrq-sz[%s]" % disk, diskinfodict[disk][6]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.avgqu-sz[%s]" % disk, diskinfodict[disk][7]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.await[%s]" % disk, diskinfodict[disk][8]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.r_await[%s]" % disk, diskinfodict[disk][9]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.w_await[%s]" % disk, diskinfodict[disk][10]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.svctm[%s]" % disk, diskinfodict[disk][11]))
        packet.append(ZabbixMetric(hostname, "custom.vfs.dev.iostat.util[%s]" % disk, diskinfodict[disk][12]))


def generate_devstat_packet(hostname):
    global packet

    args="find /sys/class/block/*/stat -type f -print |xargs awk '{print FILENAME, $0}'"
    infolist=Popen(args, stdout=PIPE, shell=True).stdout.read().decode()

    for line in infolist.split('\n'):
        if (line):
            linelist=line.split()
            diskname=linelist[0].split('/')[4]
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.read.ops[%s]" % diskname, linelist[1]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.read.merged[%s]" % diskname, linelist[2]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.read.sectors[%s]" % diskname, linelist[3]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.read.ms[%s]" % diskname, linelist[4]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.write.ops[%s]" % diskname, linelist[5]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.write.merged[%s]" % diskname, linelist[6]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.write.sectors[%s]" % diskname, linelist[7]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.write.ms[%s]" % diskname, linelist[8]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.io.active[%s]" % diskname, linelist[9]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.io.ms[%s]" % diskname, linelist[10]))
            packet.append(ZabbixMetric(hostname, "custom.vfs.dev.weight.io.ms[%s]" % diskname, linelist[11]))


def main():
    global packet
    global hostname

    t1 = Process(target=generate_iostat_packet, args=(hostname,), daemon=True)
    t2 = Process(target=generate_sar_packet, args=(hostname,), daemon=True)
    t3 = Process(target=generate_devstat_packet, args=(hostname,), daemon=True)
    t1.start()
    t2.start()
    t3.start()
    t1.join()
    t2.join()
    t3.join()

    try:
        send_to_zabbix(packet, META_ZABBIX_SERVER_IP, META_ZABBIX_SERVER_PORT)
        logger.info('epmmm: send to new zabbix')

    except Exception as e:
        logger.error('epmmm: %s. %s!' % ( hostname, e))

if __name__ == '__main__':
    main()
