epmmm performance monitor mysql(mysql, mariadb, percona), memcached, redis, tendis, numa cpu, linux tcp status, linux disk stats for zabbix 2.4 above

This is easy to monitor one physical machine with multiple mysql instances, multiple redis instances, multiple memcached instances, multiple tendis instances.

Authors: earl86

link：

https://github.com/earl86/epmmm

Info: The scripts only tested on python 3


Using:

install python3 and pip3

yum install python3-devel gcc gcc-c++

pip3 install py-zabbix

pip3 install argparse

pip3 install strip_ansi

pip3 install pexpect

pip3 install pymemcache

pip3 install PyMySQL

pip3 install redis

you may be need to link file:

ln -s /usr/local/mysql/lib/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.18


The wrapper *.sh for zabbix agent call script.

Zabbix server call agent runs the wrapper *.sh script every 5 seconds. and zabbix agent node put data to zabbix server in trapper mode.


On zabbix server test the script using:

MySQL:

zabbix_get -s 192.168.0.1 -p 10050 -k "epmmm.mysql.check[zabbixmysql,192.168.0.1,3306,check]"

python epmmm_get_mysql_stats.py --servicehostname $SERVICEHOSTNAME --serviceip $SERVICEIP --serviceport $SERVICEPORT --username $USERNAME --password $PASSWORD --zabbixserver $ZABBIXSERVER --zabbixserver_port $ZABBIXSERVER_PORT

The script need zabbix_sender and Python3 Running Environment

The default monitor mysql port is 3306, if you need to monitor other port, you need to add the Inherited and host macros:{$MYSQL_PORT}=xxxx on the monitor Host

Remember to change the USERNAME PASSWORD ZABBIXSERVER for your's.

Import the template into zabbix web.

put the following three scripts on the mysql server which has zabbix agent

/etc/zabbix/zabbix_agentd.d/userparameter_epmmm_mysql.conf

/etc/zabbix/scripts/epmmm_get_mysql_stats_wrapper.sh

/etc/zabbix/scripts/epmmm_get_mysql_stats.py

restart the zabbix agent service

Add the mysqlservice on zabbix web 

Enjoy it!


Memcached Redis Tendis etc.:

use like MySQL 


