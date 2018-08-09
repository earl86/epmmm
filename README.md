# epmmm for zabbix 3.x and 2.x
epmmm for mysql and mariadb performance monitor. 


The wrapper for zabbix python script.


It runs the script every 10 seconds. and parses the cache file on each following run.


Test the script using: 

zabbix_get -s 192.168.0.1 -p 10050 -k "epmmm.mysql.check[zabbixmysql,192.168.0.1,3306,check]"

python epmmm_get_mysql_stats.py -servicehostname SERVICEHOSTNAME --servicehost SERVICEHOST --serviceport SERVICEPORT --username USERNAME --password PASSWORD

The script need zabbix_sender and Python Running Environment


The default monitor mysql port is 3306, if need to monitor other port, you need to add the Inherited and host macros:{$MYSQL_PORT}=xxxx on the monitor Host


Remember to change the USERNAME PASSWORD ZABBIXSERVER for your's.


Authors: earl86

using:

/etc/zabbix/zabbix_agentd.d/userparameter_epmmm_mysql.conf

/etc/zabbix/scripts/epmmm_get_mysql_stats_wrapper.sh

/etc/zabbix/scripts/epmmm_get_mysql_stats.py
