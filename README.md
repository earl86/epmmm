epmmm performance monitor mysql, mariadb, memcached and redis for zabbix 2.x and zabbix 3.x

link：

https://github.com/earl86/epmmm

The wrapper for zabbix python script.

It runs the script every 10 seconds. and parses the cache file on each following run.

Test the script using:

zabbix_get -s 192.168.0.1 -p 10050 -k "epmmm.mysql.check[zabbixmysql,192.168.0.1,3306,check]"

python epmmm_get_mysql_stats.py --servicehostname $SERVICEHOSTNAME --serviceip $SERVICEIP --serviceport $SERVICEPORT --username $USERNAME --password $PASSWORD --zabbixserver $ZABBIXSERVER --zabbixserver_port $ZABBIXSERVER_PORT

The script need zabbix_sender and Python Running Environment

The default monitor mysql port is 3306, if you need to monitor other port, you need to add the Inherited and host macros:{$MYSQL_PORT}=xxxx on the monitor Host

Remember to change the USERNAME PASSWORD ZABBIXSERVER for your's.

Authors: earl86

info:the scripts only tested on python 2.6 and python 2.7 and python 3


using:

install python and pip

yum install python-devel gcc gcc-c++

pip install MySQL-python

pip install argparse

you may be need to link file:
ln -s /usr/local/mysql/lib/libmysqlclient.so.18 /usr/lib64/libmysqlclient.so.18



import the template into zabbix


put the following three scripts on zhe mysql server which has zabbix agent

/etc/zabbix/zabbix_agentd.d/userparameter_epmmm_mysql.conf

/etc/zabbix/scripts/epmmm_get_mysql_stats_wrapper.sh

/etc/zabbix/scripts/epmmm_get_mysql_stats.py


restart the zabbix agent service


add the mysqlservice and mysqlhost on zabbix web 

Enjoy it
