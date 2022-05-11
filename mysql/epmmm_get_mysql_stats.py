#!/usr/bin/python
#coding=utf-8
#encoding:utf8
#The user to monitor Your MySQL Service.
#GRANT PROCESS, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'zabbix'@'%' IDENTIFIED BY 'zabbix';
#test use: python3 epmmm_get_mysql_stats-python3.py --servicehostname your_mysqlservice_hostname --serviceip 192.168.1.200 --serviceport 3306 --username zabbix --password zabbix --zabbixserver 192.168.1.2 --zabbixserver_port 10051
#important: your_mysqlservice_hostname must be the same as in your zabbix hostname config.
#pip3 install PyMySQL
#pip3 install argparse
#pip3 install py-zabbix

import os
import re
import math
import subprocess
from subprocess import Popen
from subprocess import PIPE
import logging
import pymysql
import argparse
from pyzabbix.sender import ZabbixMetric, ZabbixSender
import unicodedata
import hashlib

parser = argparse.ArgumentParser()
parser.add_argument("--servicehostname", action="store", dest='servicehostname', help="input the database servcie hostname", required=True)
parser.add_argument("--serviceip", action="store", dest='serviceip', help="input the database servcie host", required=True)
parser.add_argument("--serviceport", action="store", dest='serviceport', type=int, help="input the database service port", required=True)
parser.add_argument("--username", action="store", dest='username', help="input the monitor user name for database", required=True)
parser.add_argument("--password", action="store", dest='password', help="input the user's password", required=True)
parser.add_argument("--zabbixserver", action="store", dest='zabbixserver', help="input the Zabbix Server IP", required=True)
parser.add_argument("--zabbixserver_port", action="store", dest='zabbixserver_port', type=int, help="input the Zabbix Server Port", required=True)
args = parser.parse_args()

SERVICEHOSTNAME=args.servicehostname
SERVICEIP=args.serviceip
SERVICEPORT=args.serviceport
USERNAME=args.username
PASSWORD=args.password
ZABBIX_SERVER=args.zabbixserver
ZABBIX_SERVER_PORT=args.zabbixserver_port

logging.basicConfig(level=logging.INFO,
                    filename='/var/log/zabbix/epmmm-get-mysql-stats.log',
                    datefmt='%Y/%m/%d %H:%M:%S',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')

logger = logging.getLogger(__name__)

def send_to_zabbix(packet):
    server = ZabbixSender(ZABBIX_SERVER,ZABBIX_SERVER_PORT)
    server.send(packet)



def generate_packet(SERVICEHOSTNAME,resaultdic):
    packet = []
    for key in resaultdic.keys():
        packet.append(ZabbixMetric(SERVICEHOSTNAME, "epmmm.mysql.%s" % key,str(resaultdic[key] if resaultdic[key]!='' else 0)))

    return packet


def get_mysql_status(querysql):
    try:
        conn = pymysql.connect(host=SERVICEIP, port=SERVICEPORT, user=USERNAME, passwd=PASSWORD,db='',charset="latin1",connect_timeout=3)
        cursor = conn.cursor()
        cursor.execute(querysql)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.info('epmmm %s, %s, %s!', SERVICEHOSTNAME, e, querysql)
    else:
        return result

def get_mysql_status_dic(querysql):
    try:
        conn = pymysql.connect(host=SERVICEIP, port=SERVICEPORT, user=USERNAME, passwd=PASSWORD,db='',charset="latin1",connect_timeout=3)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(querysql)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.info('epmmm %s, %s, %s!', SERVICEHOSTNAME, e, querysql)
    else:
        return result

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False

def increment(statusdic, key, howmuch):
    if (key in statusdic):
        statusdic[key]=statusdic[key]+howmuch
        return statusdic
    else:
        statusdic[key]=howmuch
        return statusdic

def to_float(rownum):
    rownum = re.findall('[\d+\.\d]*',rownum)
    try:
        f = float(rownum[0])
    except Exception as e:
        logger.info('epmmm %s, %s, %s!', SERVICEHOSTNAME, rownum, e)
        return 0.0
    return f

def to_int(rownum):
    rownum = re.findall('[-+?\d+\.\d]*',rownum)
    return int(float(rownum[0]))

def get_resaultdic():
    txn_seen=False
    prev_line=''
    MasterStatus={}
    SlaveStatus={}
    GlobalStatus={}
    GlobalVariables={}
    InnodbStatus={}
    MysqlStatus={}

    MysqlStatus['agent_OK']=1

    resaults=get_mysql_status_dic('show master status;')
    if (resaults is not None):
        for resault in resaults:
            MasterStatus['Binlog_position'] = resault['Position']
            MasterStatus['Binlog_file'] = resault['File']
            MasterStatus['Binlog_number'] = to_int(resault['File'].split('.')[1])
            MasterStatus['Binlog_do_filter'] = resault['Binlog_Do_DB']
            MasterStatus['Binlog_ignore_filter'] = resault['Binlog_Ignore_DB']


    resaults=get_mysql_status('show binary logs;')
    MasterStatus['Binlog_count']=0
    MasterStatus['Binlog_total_size']=0
    if (resaults is not None):
        for resault in resaults:
            MasterStatus['Binlog_count'] += 1
            MasterStatus['Binlog_total_size'] += resault[1]


    resaults=get_mysql_status('show slave hosts;')
    MasterStatus['Slave_count']=0
    if (resaults is not None):
        for resault in resaults:
            MasterStatus['Slave_count'] += 1

    resaults=get_mysql_status_dic('show slave status;')
    # Scale slave_running and slave_stopped relative to the slave lag.
    if (resaults is not None):
        for resault in resaults:
            SlaveStatus['Master_Log_File']=to_int(resault['Master_Log_File'].split(".")[1])
            SlaveStatus['Relay_Master_Log_File']=to_int(resault['Relay_Master_Log_File'].split(".")[1])
            SlaveStatus['Relay_Log_File']=to_int(resault['Relay_Log_File'].split(".")[1])
            if(resault['Slave_IO_Running']=='Yes'):
                SlaveStatus['Slave_IO_Running']=1
            else:
                SlaveStatus['Slave_IO_Running']=0

            if(resault['Slave_SQL_Running']=='Yes'):
                SlaveStatus['Slave_SQL_Running']=1
            else:
                SlaveStatus['Slave_SQL_Running']=0

            SlaveStatus['Read_Master_Log_Pos']=resault['Read_Master_Log_Pos']
            SlaveStatus['Exec_Master_Log_Pos']=resault['Exec_Master_Log_Pos']
            SlaveStatus['Relay_Log_Pos']=resault['Relay_Log_Pos']
            SlaveStatus['Relay_Log_Space']=resault['Relay_Log_Space']
            SlaveStatus['Seconds_Behind_Master']=resault['Seconds_Behind_Master']

        SlaveStatus['slave_lag_binlog']=SlaveStatus['Master_Log_File']-SlaveStatus['Relay_Master_Log_File']

        if(SlaveStatus['slave_lag_binlog']==0):
            SlaveStatus['slave_binlog_pos_lag']=SlaveStatus['Read_Master_Log_Pos']-SlaveStatus['Exec_Master_Log_Pos']
        else:
            SlaveStatus['slave_binlog_pos_lag']=(SlaveStatus['slave_lag_binlog']-1)*1073748717+SlaveStatus['Read_Master_Log_Pos']+(1073748717-SlaveStatus['Exec_Master_Log_Pos'])


    resaults=get_mysql_status('show global status;')
    if (resaults is not None):
        MysqlStatus['alive']=1
        for resault in resaults:
            if ( is_number(resault[1])):
                GlobalStatus[resault[0]]=to_int(resault[1])
        #mariadb
        if( not 'Access_denied_errors' in GlobalStatus):
            GlobalStatus['Access_denied_errors']=0
        if( not 'Binlog_bytes_written' in GlobalStatus):
            GlobalStatus['Binlog_bytes_written']=0
        if( not 'Key_blocks_warm' in GlobalStatus):
            GlobalStatus['Key_blocks_warm']=0



    resaults=get_mysql_status('show global variables;')
    if (resaults is not None):
        for resault in resaults:
            if(resault[0]=='max_connections'):
                GlobalVariables['max_connections']=to_int(resault[1])
            elif(resault[0]=='innodb_log_buffer_size'):
                GlobalVariables['innodb_log_buffer_size']=to_int(resault[1])
            elif(resault[0]=='key_buffer_size'):
                GlobalVariables['key_buffer_size']=to_int(resault[1])
            elif(resault[0]=='key_cache_block_size'):
                GlobalVariables['key_cache_block_size']=to_int(resault[1])
            elif(resault[0]=='innodb_page_size'):
                GlobalVariables['innodb_page_size']=to_int(resault[1])
            elif(resault[0]=='query_cache_size'):
                GlobalVariables['query_cache_size']=to_int(resault[1])
            elif(resault[0]=='table_open_cache'):
                GlobalVariables['table_open_cache']=to_int(resault[1])
            elif(resault[0]=='thread_cache_size'):
                GlobalVariables['thread_cache_size']=to_int(resault[1])
            elif(resault[0]=='character_set_server'):
                GlobalVariables['character_set_server']=resault[1]
            elif(resault[0]=='datadir'):
                GlobalVariables['datadir']=resault[1]
            elif(resault[0]=='default_storage_engine'):
                GlobalVariables['default_storage_engine']=resault[1]
            elif(resault[0]=='event_scheduler'):
                GlobalVariables['event_scheduler']=resault[1]
            elif(resault[0]=='foreign_key_checks'):
                GlobalVariables['foreign_key_checks']=resault[1]
            elif(resault[0]=='general_log'):
                GlobalVariables['general_log']=resault[1]
            elif(resault[0]=='log_output'):
                GlobalVariables['log_output']=resault[1]
            elif(resault[0]=='log_queries_not_using_indexes'):
                GlobalVariables['log_queries_not_using_indexes']=resault[1]
            elif(resault[0]=='log_slave_updates'):
                GlobalVariables['log_slave_updates']=resault[1]
            elif(resault[0]=='log_warnings'):
                GlobalVariables['log_warnings']=resault[1]
            elif(resault[0]=='long_query_time'):
                GlobalVariables['long_query_time']=resault[1]
            elif(resault[0]=='max_allowed_packet'):
                GlobalVariables['max_allowed_packet']=resault[1]
            elif(resault[0]=='innodb_buffer_pool_instances'):
                GlobalVariables['innodb_buffer_pool_instances']=resault[1]
            elif(resault[0]=='innodb_buffer_pool_size'):
                GlobalVariables['innodb_buffer_pool_size']=resault[1]
            elif(resault[0]=='innodb_file_format'):
                GlobalVariables['innodb_file_format']=resault[1]
            elif(resault[0]=='innodb_file_per_table'):
                GlobalVariables['innodb_file_per_table']=resault[1]
            elif(resault[0]=='innodb_flush_log_at_trx_commit'):
                GlobalVariables['innodb_flush_log_at_trx_commit']=resault[1]
            elif(resault[0]=='innodb_flush_method'):
                GlobalVariables['innodb_flush_method']=resault[1]
            elif(resault[0]=='innodb_force_recovery'):
                GlobalVariables['innodb_force_recovery']=resault[1]
            elif(resault[0]=='innodb_io_capacity'):
                GlobalVariables['innodb_io_capacity']=resault[1]
            elif(resault[0]=='innodb_log_files_in_group'):
                GlobalVariables['innodb_log_files_in_group']=resault[1]
            elif(resault[0]=='innodb_log_file_size'):
                GlobalVariables['innodb_log_file_size']=resault[1]
            elif(resault[0]=='ignore_builtin_innodb'):
                GlobalVariables['ignore_builtin_innodb']=resault[1]
            elif(resault[0]=='max_heap_table_size'):
                GlobalVariables['max_heap_table_size']=resault[1]
            elif(resault[0]=='max_sort_length'):
                GlobalVariables['max_sort_length']=resault[1]
            elif(resault[0]=='max_user_connections'):
                GlobalVariables['max_user_connections']=resault[1]
            elif(resault[0]=='open_files_limit'):
                GlobalVariables['open_files_limit']=resault[1]
            elif(resault[0]=='query_cache_type'):
                GlobalVariables['query_cache_type']=resault[1]
            elif(resault[0]=='read_buffer_size'):
                GlobalVariables['read_buffer_size']=resault[1]
            elif(resault[0]=='skip_networking'):
                GlobalVariables['skip_networking']=resault[1]
            elif(resault[0]=='slow_query_log'):
                GlobalVariables['slow_query_log']=resault[1]
            elif(resault[0]=='sort_buffer_size'):
                GlobalVariables['sort_buffer_size']=resault[1]
            elif(resault[0]=='sql_mode'):
                GlobalVariables['sql_mode']=resault[1]
            elif(resault[0]=='table_cache'):
                GlobalVariables['table_cache']=resault[1]
            elif(resault[0]=='table_definition_cache'):
                GlobalVariables['table_definition_cache']=resault[1]
            elif(resault[0]=='tmp_table_size'):
                GlobalVariables['tmp_table_size']=resault[1]
            elif(resault[0]=='thread_cache_size'):
                GlobalVariables['thread_cache_size']=resault[1]
            elif(resault[0]=='thread_stack'):
                GlobalVariables['thread_stack']=resault[1]
            elif(resault[0]=='tx_isolation'):
                GlobalVariables['tx_isolation']=resault[1]
            elif(resault[0]=='version'):
                GlobalVariables['version']=resault[1]
            elif(resault[0]=='flush_time'):
                GlobalVariables['flush_time']=resault[1]
            elif(resault[0]=='innodb_max_dirty_pages_pct'):
                GlobalVariables['innodb_max_dirty_pages_pct']=to_int(resault[1])
            elif(resault[0]=='auto_increment_increment'):
                GlobalVariables['auto_increment_increment']=resault[1]
            elif(resault[0]=='auto_increment_offset'):
                GlobalVariables['auto_increment_offset']=resault[1]
            elif(resault[0]=='binlog_row_image'):
                GlobalVariables['binlog_row_image']=resault[1]
            elif(resault[0]=='binlog_format'):
                GlobalVariables['binlog_format']=resault[1]
            elif(resault[0]=='binlog_cache_size'):
                GlobalVariables['binlog_cache_size']=resault[1]
            elif(resault[0]=='binlog_stmt_cache_size'):
                GlobalVariables['binlog_stmt_cache_size']=resault[1]
            elif(resault[0]=='expire_logs_days'):
                GlobalVariables['expire_logs_days']=resault[1]
            elif(resault[0]=='log_bin'):
                GlobalVariables['log_bin']=resault[1]
            elif(resault[0]=='sync_binlog'):
                GlobalVariables['sync_binlog']=resault[1]
            elif(resault[0]=='sync_master_info'):
                GlobalVariables['sync_master_info']=resault[1]
            elif(resault[0]=='read_only'):
                GlobalVariables['read_only']=resault[1]
            elif(resault[0]=='sync_relay_log'):
                GlobalVariables['sync_relay_log']=resault[1]
            elif(resault[0]=='sync_relay_log_info'):
                GlobalVariables['sync_relay_log_info']=resault[1]
            elif(resault[0]=='slave_skip_errors'):
                GlobalVariables['slave_skip_errors']=resault[1]


        GlobalVariables['key_buffer_blocks']=GlobalVariables['key_buffer_size']/GlobalVariables['key_cache_block_size']
        GlobalStatus['Key_blocks_used_now']=GlobalVariables['key_buffer_blocks']-GlobalStatus['Key_blocks_unused']
        GlobalStatus['Key_blocks_not_flushed_b'] = GlobalVariables['key_cache_block_size'] * GlobalStatus['Key_blocks_not_flushed'];
        GlobalStatus['Key_blocks_unused_b'] = GlobalVariables['key_cache_block_size'] * GlobalStatus['Key_blocks_unused'];
        GlobalStatus['Key_blocks_used_b'] = GlobalVariables['key_cache_block_size'] * GlobalStatus['Key_blocks_used'];
        GlobalStatus['Key_blocks_used_now_b'] = GlobalVariables['key_cache_block_size'] * GlobalStatus['Key_blocks_used_now'];
        #mariadb
        GlobalStatus['Key_blocks_warm_b'] = GlobalVariables['key_cache_block_size'] * GlobalStatus['Key_blocks_warm'];
        if ( (GlobalStatus['Key_read_requests'] + GlobalStatus['Key_reads']) == 0 ):
            GlobalStatus['Key_buffer_hit_rate'] = 0.0
        else:
            GlobalStatus['Key_buffer_hit_rate'] = round(GlobalStatus['Key_read_requests'] * 100.00 / (GlobalStatus['Key_read_requests'] + GlobalStatus['Key_reads']), 2)

        if ( len(re.findall('([0-9]{1,2}).([0-9]{1,2}).([0-9]{1,2})', GlobalVariables['version']))>0):
            march=re.findall('([0-9]{1,2}).([0-9]{1,2}).([0-9]{1,2})', GlobalVariables['version'])
            GlobalVariables['mr_version'] = '%s%s' %(march[0][0],march[0][1])
        else:
            GlobalVariables['mr_version'] = '56'

        GlobalStatus['Qcache_used_blocks'] = GlobalStatus['Qcache_total_blocks'] - GlobalStatus['Qcache_free_blocks']
        GlobalStatus['Qcache_used_memory'] = GlobalVariables['query_cache_size'] - GlobalStatus['Qcache_free_memory']
        if ( GlobalStatus['Qcache_used_blocks'] == 0 ):
            GlobalStatus['Qcache_byte_per_block'] = 0
        else:
            GlobalStatus['Qcache_byte_per_block'] = int(GlobalStatus['Qcache_used_memory'] / GlobalStatus['Qcache_used_blocks'])

        if ( GlobalStatus['Qcache_queries_in_cache'] == 0 ):
            GlobalStatus['Qcache_block_per_query'] = 0
        else:
            GlobalStatus['Qcache_block_per_query'] = int(GlobalStatus['Qcache_used_blocks'] / GlobalStatus['Qcache_queries_in_cache'])



    resaults=get_mysql_status('show engine innodb status;')
    if (resaults is not None):
        lines=resaults[0][2].split("\n")
        for line in lines:
            line=line.strip()
            row=' '.join(line.split())
            row= row.split()
            if (line.find("Mutex spin waits") == 0):
                # Mutex spin waits 79626940, rounds 157459864, OS waits 698719
                InnodbStatus['Innodb_mutex_spin_waits']=to_int(row[3])
                InnodbStatus['Innodb_mutex_rounds']=to_int(row[5])
                InnodbStatus['Innodb_mutex_os_waits']=to_int(row[8])
            elif (line.find("RW-shared spins") == 0 and line.find(";") > 0):
                # RW-shared spins 3859028, OS waits 2100750; RW-excl spins 4641946, OS waits 1530310
                InnodbStatus['Innodb_rw-shared_spins']=to_int(row[2])
                InnodbStatus['Innodb_rw-shared_os_waits']=to_int(row[5])
                InnodbStatus['Innodb_rw-excl_spins']=to_int(row[8])
                InnodbStatus['Innodb_rw-excl_os_waits']=to_int(row[11])
            elif (line.find("RW-shared spins") == 0 and line.find("; RW-excl spins") < 0):
                # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                # RW-shared spins 604733, rounds 8107431, OS waits 241268
                InnodbStatus['Innodb_rw-shared_spins']=to_int(row[2])
                InnodbStatus['Innodb_rw-shared_rounds']=to_int(row[4])
                InnodbStatus['Innodb_rw-shared_os_waits']=to_int(row[7])
            elif (line.find("RW-excl spins") == 0):
                # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                # RW-excl spins 604733, rounds 8107431, OS waits 241268
                InnodbStatus['Innodb_rw-excl_spins']=to_int(row[2])
                InnodbStatus['Innodb_rw-excl_rounds']=to_int(row[4])
                InnodbStatus['Innodb_rw-excl_os_waits']=to_int(row[7])
            elif (line.find("RW-sx spins") == 0):
                # Post 5.5.17 SHOW ENGINE INNODB STATUS syntax
                # RW-sx spins 1014, rounds 6472, OS waits 134
                InnodbStatus['Innodb_rw-sx_spins']=to_int(row[2])
                InnodbStatus['Innodb_rw-sx_rounds']=to_int(row[4])
                InnodbStatus['Innodb_rw-sx_os_waits']=to_int(row[7])
            elif (line.find("History list length") == 0):
                #History list length 2356
                InnodbStatus['Innodb_trx_history_list_length']=to_int(row[3])
            elif (line.find("seconds the semaphore:") > 0):
                # --Thread 907205 has waited at handler/ha_innodb.cc line 7156 for 1.00 seconds the semaphore:
                InnodbStatus=increment(InnodbStatus,'innodb_sem_waits',1)
                try:
                    InnodbStatus=increment(InnodbStatus,'innodb_sem_wait_time_ms',to_int(str(to_float(row[9])*1000)))
                except Exception as e:
                    logger.info('epmmm %s, %s!', SERVICEHOSTNAME, e)
            elif (line.find("Trx id counter") == 0):
                # --Thread 907205 has waited at handler/ha_innodb.cc line 7156 for 1.00 seconds the semaphore:
                InnodbStatus['innodb_transactions']=to_int(row[3])
                txn_seen=True
            elif(line.find("Purge done for trx") == 0):
                #Purge done for trx's n:o < 2807498 undo n:o < 0 state: running but idle
                InnodbStatus['purged_txns']=to_int(row[6])
                InnodbStatus['unpurged_txns']=to_int(row[10])
            elif(line.find("History list length") == 0):
                # History list length 132
                InnodbStatus['history_list']=to_int(row[3])
            elif( txn_seen and line.find("---TRANSACTION") == 0):
                InnodbStatus=increment(InnodbStatus,'current_transactions',1)
                if(line.find("ACTIVE") > 0):
                    InnodbStatus=increment(InnodbStatus,'active_transactions',1)
            elif( txn_seen and line.find("------- TRX HAS BEEN") == 0):
                # ------- TRX HAS BEEN WAITING 32 SEC FOR THIS LOCK TO BE GRANTED:
                InnodbStatus=increment(InnodbStatus,'innodb_lock_wait_secs',to_int(row[5]))
            elif( line.find("mysql tables in use") == 0 ):
                # mysql tables in use 2, locked 2
                InnodbStatus['innodb_tables_in_use']=to_int(row[4])
                InnodbStatus['innodb_locked_tables']=to_int(row[6])
            elif( txn_seen and line.find("lock struct(s)") > 0):
                # 23 lock struct(s), heap size 3024, undo log entries 27
                # LOCK WAIT 12 lock struct(s), heap size 3024, undo log entries 5
                # LOCK WAIT 2 lock struct(s), heap size 368
                if(line.find("LOCK WAIT")==0):
                    InnodbStatus=increment(InnodbStatus,'innodb_lock_structs',to_int(row[2]))
                    InnodbStatus=increment(InnodbStatus,'locked_transactions',1)
                else:
                    InnodbStatus=increment(InnodbStatus,'locked_transactions',to_int(row[0]))
            elif(line.find("Pending normal aio reads:")==0):
                if(GlobalVariables['mr_version'] == '57'):
                    #Pending normal aio reads: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] , aio writes: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] ,
                    ia = line.split(": [")[1].split("] ,")[0].split(", ")
                    iw = line.split(": [")[2].split("] ,")[0].split(", ")
                    iasum = 0
                    iwsum = 0
                    for a in ia:
                        iasum += to_int(a)
                    for w in iw:
                        iwsum += to_int(w)
                    InnodbStatus['pending_normal_aio_reads'] = iasum
                    InnodbStatus['pending_normal_aio_writes'] = iwsum
                else:
                    # Pending normal aio reads: 0, aio writes: 0,
                    InnodbStatus['pending_normal_aio_reads']=to_int(row[4])
                    InnodbStatus['pending_normal_aio_writes']=to_int(row[7])
            elif(line.find("ibuf aio reads")==0):
                if(GlobalVariables['mr_version'] == '57'):
                    # ibuf aio reads:, log i/o's:, sync i/o's:
                    InnodbStatus['pending_ibuf_aio_reads']=0
                    InnodbStatus['pending_aio_log_ios']=0
                    InnodbStatus['pending_aio_sync_ios']=0
                else:
                    #  ibuf aio reads: 0, log i/o's: 0, sync i/o's: 0
                    InnodbStatus['pending_ibuf_aio_reads']=to_int(row[3])
                    InnodbStatus['pending_aio_log_ios']=to_int(row[6])
                    InnodbStatus['pending_aio_sync_ios']=to_int(row[9])
            elif(line.find("Pending flushes (fsync)")==0):
                # Pending flushes (fsync) log: 0; buffer pool: 0
                InnodbStatus['pending_log_flushes']=to_int(row[4])
                InnodbStatus['pending_buf_pool_flushes']=to_int(row[7])
            elif(line.find(" OS file reads, ")>0):
                # 8782182 OS file reads, 15635445 OS file writes, 947800 OS fsyncs
                InnodbStatus['Innodb_os_file_reads']=to_int(row[0])
                InnodbStatus['Innodb_os_file_writes']=to_int(row[4])
                InnodbStatus['Innodb_os_fsyncs']=to_int(row[8])
            elif(line.find(" avg bytes/read, ")>0):
                #0.25 reads/s, 16384 avg bytes/read, 1803.80 writes/s, 82.98 fsyncs/s
                InnodbStatus['Innodb_os_file_reads_ps']=to_float(row[0])
                InnodbStatus['Innodb_os_file_bytes_read_ps']=to_int(row[2])
                InnodbStatus['Innodb_os_file_writes_ps']=to_float(row[5])
                InnodbStatus['Innodb_os_fsyncs_ps']=to_float(row[7])
            # INSERT BUFFER AND ADAPTIVE HASH INDEX
            elif(line.find("Ibuf for space 0: size ")==0):
                # Older InnoDB code seemed to be ready for an ibuf per tablespace.  It
                # had two lines in the output.  Newer has just one line, see below.
                # Ibuf for space 0: size 1, free list len 887, seg size 889, is not empty
                # Ibuf for space 0: size 1, free list len 887, seg size 889,
                InnodbStatus['ibuf_used_cells']=to_int(row[5])
                InnodbStatus['ibuf_free_cells']=to_int(row[9])
                InnodbStatus['ibuf_cell_count']=to_int(row[12])
            elif(line.find("Ibuf: size ")==0):
                # Ibuf: size 1, free list len 4634, seg size 4636,
                InnodbStatus['ibuf_used_cells']=to_int(row[2])
                InnodbStatus['ibuf_free_cells']=to_int(row[6])
                InnodbStatus['ibuf_cell_count']=to_int(row[9])
                if(line.find("merges")):
                    InnodbStatus['ibuf_merges']=to_int(row[10])
            elif(line.find(", delete mark ")>0 and prev_line.find("merged operations:")==0):
                # Output of show engine innodb status has changed in 5.5
                # merged operations:
                # insert 593983, delete mark 387006, delete 73092
                InnodbStatus['ibuf_inserts']=to_int(row[1])
                InnodbStatus['ibuf_merged']=to_int(row[1]) + to_int(row[4]) + to_int(row[6])
            elif(line.find(" merged recs, ")==0):
                # 19817685 inserts, 19817684 merged recs, 3552620 merges
                InnodbStatus['ibuf_inserts']=to_int(row[0])
                InnodbStatus['ibuf_merged']=to_int(row[2])
                InnodbStatus['ibuf_merges']=to_int(row[5])
            elif(line.find("Hash table size ")==0):
                # In some versions of InnoDB, the used cells is omitted.
                # Hash table size 57374437, node heap has 72964 buffer(s) <-- no used cells
                InnodbStatus['hash_table_size']=to_int(row[3])
                if(line.find("node heap has")>0):
                    InnodbStatus['Innodb_hash_node_size']=to_int(row[7])*GlobalVariables['innodb_page_size']
                if(line.find("used cells")>0):
                    InnodbStatus['hash_index_cells_used']=to_int(row[6])
                else:
                    InnodbStatus['hash_index_cells_used']=0
            elif(line.find("hash searches/s")>0):
                #2225.77 hash searches/s, 71.93 non-hash searches/s
                try:
                    InnodbStatus['Innodb_hash_searches']=to_float(row[0])
                    InnodbStatus['Innodb_non_hash_searches']=to_float(row[3])
                except Exception as e:
                    logger.info('epmmm %s, %s!', SERVICEHOSTNAME, e)
            # LOG
            elif(line.find(" pending log writes, ")>0):
                # 0 pending log writes, 0 pending chkp writes
                InnodbStatus['pending_log_writes']=to_int(row[0])
                InnodbStatus['pending_chkp_writes']=to_int(row[4])
            elif(line.find(" log i/o's done, ")>0):
                # 3430041 log i/o's done, 17.44 log i/o's/second
                # 520835887 log i/o's done, 17.28 log i/o's/second, 518724686 syncs, 2980893 checkpoints
                InnodbStatus['log_writes']=to_int(row[0])
                InnodbStatus['log_writes_ps']=to_int(row[4])
            elif(line.find("Log sequence number")==0):
                # This number is NOT printed in hex in InnoDB plugin.
                # Log sequence number 13093949495856 //plugin
                # Log sequence number 125 3934414864 //normal
                try:
                    row[4]
                    InnodbStatus['Innodb_log_sequence_number']=to_int(row[3]) + to_int(row[4])
                except IndexError:
                    InnodbStatus['Innodb_log_sequence_number']=to_int(row[3])
            elif(line.find("Log flushed up to")==0):
                # This number is NOT printed in hex in InnoDB plugin.
                # Log flushed up to   13093948219327
                # Log flushed up to   125 3934414864
                try:
                    row[5]
                    InnodbStatus['Innodb_log_flushed_up_to']=to_int(row[4]) + to_int(row[5])
                except IndexError:
                    InnodbStatus['Innodb_log_flushed_up_to']=to_int(row[4])
            elif(line.find("Pages flushed up to")==0):
                # This number is NOT printed in hex in InnoDB plugin.
                # Log flushed up to   13093948219327
                # Log flushed up to   125 3934414864
                try:
                    row[5]
                    InnodbStatus['Innodb_pages_flushed_up_to']=to_int(row[4]) + to_int(row[5])
                except IndexError:
                    InnodbStatus['Innodb_pages_flushed_up_to']=to_int(row[4])
            elif(line.find("Last checkpoint at")==0):
                # Last checkpoint at  125 3934293461
                try:
                    row[4]
                    InnodbStatus['Innodb_last_checkpoint_at']=to_int(row[3]) + to_int(row[4])
                except IndexError:
                    InnodbStatus['Innodb_last_checkpoint_at']=to_int(row[3])
            # BUFFER POOL AND MEMORY
            elif(line.find("Total memory allocated")==0 and line.find("in additional pool allocated")>0):
                # Total memory allocated 29642194944; in additional pool allocated 0
                # Total memory allocated by read views 96
                InnodbStatus['total_mem_alloc']=to_int(row[3])
                InnodbStatus['additional_pool_alloc']=to_int(row[8])
            elif(line.find("Adaptive hash index")==0):
                #Adaptive hash index 19057200        (18921928 + 135272)
                InnodbStatus['adaptive_hash_memory']=to_int(row[3])
            elif(line.find("Page hash           ")==0):
                #   Page hash           11688584
                InnodbStatus['page_hash_memory']=to_int(row[2])
            elif(line.find("Dictionary cache    ")==0):
                #   Dictionary cache    145525560     (140250984 + 5274576)
                InnodbStatus['dictionary_cache_memory']=to_int(row[2])
            elif(line.find("File system         ")==0):
                #   File system         313848     (82672 + 231176)
                InnodbStatus['file_system_memory']=to_int(row[2])
            elif(line.find("Lock system         ")==0):
                #   Lock system         29232616     (29219368 + 13248)
                InnodbStatus['lock_system_memory']=to_int(row[2])
            elif(line.find("Recovery system     ")==0):
                #   Recovery system     0     (0 + 0)
                InnodbStatus['recovery_system_memory']=to_int(row[2])
            elif(line.find("Threads            ")==0):
                #   Threads             409336     (406936 + 2400)
                InnodbStatus['thread_hash_memory']=to_int(row[1])
            elif(line.find("innodb_io_pattern   ")==0):
                #   innodb_io_pattern   0     (0 + 0)
                InnodbStatus['innodb_io_pattern_memory']=to_int(row[1])
            elif(line.find("queries inside InnoDB")>0):
                #0 queries inside InnoDB, 0 queries in queue
                InnodbStatus['Innodb_queries_inside_innodb']=to_int(row[0])
                InnodbStatus['Innodb_queries_in_queue']=to_int(row[4])
            elif(line.find("read views open inside InnoDB")>0):
                #0 read views open inside InnoDB
                InnodbStatus['Innodb_open_read_views_inside_innodb']=to_int(row[0])
            prev_line = line

        InnodbStatus['unflushed_log']=InnodbStatus['Innodb_log_sequence_number']+InnodbStatus['Innodb_log_flushed_up_to']
        InnodbStatus['uncheckpointed_bytes']=InnodbStatus['Innodb_log_sequence_number']+InnodbStatus['Innodb_last_checkpoint_at']

        GlobalStatus['Innodb_buffer_pool_pages_data_b'] = GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_pages_data']
        GlobalStatus['Innodb_buffer_pool_pages_dirty_b'] = GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_pages_dirty']
        GlobalStatus['Innodb_buffer_pool_pages_free_b'] = GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_pages_free']
        # We get from time to time: Type of received value [3.02231454903657e+23] is not suitable...
        GlobalStatus['Innodb_buffer_pool_pages_misc_b'] = int(GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_pages_misc'])
        GlobalStatus['Innodb_buffer_pool_pages_total_b'] = GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_pages_total']

        if ( (GlobalStatus['Innodb_buffer_pool_read_requests'] + GlobalStatus['Innodb_buffer_pool_reads']) == 0 ):
            GlobalStatus['Innodb_buffer_pool_hit_ratio'] = 0.0
        else:
            #Not good because it is average over all time!
            GlobalStatus['Innodb_buffer_pool_hit_ratio'] = round(GlobalStatus['Innodb_buffer_pool_read_requests'] * 100.00 / (GlobalStatus['Innodb_buffer_pool_read_requests'] + GlobalStatus['Innodb_buffer_pool_reads']), 2)

        GlobalStatus['Innodb_buffer_pool_max_dirty_pages'] = math.floor(GlobalStatus['Innodb_buffer_pool_pages_total'] * GlobalVariables['innodb_max_dirty_pages_pct'] / 100)
        GlobalStatus['Innodb_buffer_pool_max_dirty_pages_b'] = GlobalVariables['innodb_page_size'] * GlobalStatus['Innodb_buffer_pool_max_dirty_pages']


    resaults=get_mysql_status('SELECT SUM(compress_time) AS compress_time, SUM(uncompress_time) AS uncompress_time FROM information_schema.INNODB_CMP;')
    if (resaults is not None):
        for resault in resaults:
            InnodbStatus['Innodb_compress_time']   = int(resault[0])
            InnodbStatus['Innodb_uncompress_time'] = int(resault[1])

    resaults=get_mysql_status('SELECT LOWER(REPLACE(trx_state, " ", "_")) AS state, count(*) AS cnt from information_schema.INNODB_TRX GROUP BY state ORDER BY state;')
    if (resaults is not None):
        for resault in resaults:
            InnodbStatus['Innodb_trx_' + resault[0]] = resault[1]

    resaultdic={}
    resaultdic.update(MasterStatus)
    resaultdic.update(SlaveStatus)
    resaultdic.update(GlobalStatus)
    resaultdic.update(GlobalVariables)
    resaultdic.update(InnodbStatus)
    resaultdic.update(MysqlStatus)
    return resaultdic


def main():
    resaultdic=get_resaultdic()
    try:
        packet = generate_packet(SERVICEHOSTNAME,resaultdic)
        #print(packet)
        send_to_zabbix(packet)
    except Exception as e:
        logger.info('epmmm %s, %s!', SERVICEHOSTNAME, e)
        logger.info(packet)


if __name__=='__main__':
    main()
