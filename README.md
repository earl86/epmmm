epmmm performance monitor mysql(mysql, mariadb, percona), memcached, redis, tendis, numa cpu, linux tcp status, linux disk stats for zabbix 2.4 above

This is easy to monitor one physical machine with multiple mysql instances, multiple redis instances, multiple memcached instances, multiple tendis instances.

Authors: earl86

link：

https://github.com/earl86/epmmm

Info: The scripts only tested on python 3


# Install:

install python3 and pip3 and zabbix_sender

yum install python3-devel

pip3 install py-zabbix

pip3 install argparse

pip3 install strip_ansi

pip3 install pexpect

pip3 install pymemcache

pip3 install PyMySQL

pip3 install redis

pip3 install configparser

Zabbix server call agent run the wrapper *.sh script every 10 seconds. and then zabbix agent put data to zabbix server in trapper mode.

1. Modify the zabbix_meta.ini
   
[zabbix_server]

META_ZABBIX_SERVER_IP=192.168.0.100

META_ZABBIX_SERVER_PORT=10051

3. Install the scripts and conf to zabbix agent server
4. Import the template to zabbix web
5. Restart the zabbix agent


# Using:

On zabbix server test the script using:

# MySQL:
##Zabbix agent key: 
1. epmmm.mysql.check[{HOST.NAME},{HOST.IP},{$MYSQL_PORT},check,{$SERVICEUNIQ},{$ZABBIXTYPE}]
2. epmmm.mysql.check[{HOST.NAME},{HOST.IP},{$MYSQL_PORT},mysqld_cpu_use,{$SERVICEUNIQ},{$ZABBIXTYPE}]

## Zabbix template Macros:
1. {$MYSQL_PORT} : 3306
2. {$SERVICEUNIQ}: ''
3. {$SERVICE_ROLE}: master/slave/backup
4. {$ZABBIXTYPE}: name in zabbix_meta.ini

## MySQL instance like this:
ps -ef |grep mysql

root      157401       1  0  2021 ?        00:00:00 /bin/sh /usr/local/mysql/bin/mysqld_safe --defaults-file=/etc/my-mysql-instance.cnf

mysql     159694  157401 99  2021 ?        28847-16:16:22 /usr/local/mysql/bin/mysqld --defaults-file=/etc/my-mysql-instance.cnf --basedir=/usr/local/mysql --datadir=/data/mysql/mysql-instance/data --plugin-dir=/usr/local/mysql/lib/mysql/plugin --user=mysql --log-error=/data/mysql/mysql-instance/log/log-error.log --pid-file=/data/mysql/mysql-instance/tmp/mysqld.pid --socket=/data/mysql/mysql-instance/tmp/mysql.sock --port=3306


## Add User to MySQL instance
USERNAME=zabbix
PASSWORD=zabbix@2014

## Test:
zabbix_get -s 192.168.0.1 -p 10050 -k "epmmm.mysql.check[zabbixmysql,192.168.0.1,3306,check,mysql-instance,zabbix_server]"

/usr/local/bin/python3 epmmm_get_mysql_stats.py --servicename ${SERVICENAME} --serviceip ${SERVICEIP} --serviceport ${SERVICEPORT} --username ${USERNAME} --password ${PASSWORD} --zabbix_type ${ZABBIXTYPE}

The default monitor mysql port is 3306, if you need to monitor other port, you need to add the Inherited and host macros:{$MYSQL_PORT}=xxxx on the monitor Host


Enjoy it!


# Memcached Redis Tendis etc.:

use like MySQL 


