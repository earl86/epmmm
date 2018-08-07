# epmmm
epmmm for mysql and mariadb performance monitor.
The wrapper for zabbix python script.
It runs the script every 30 seconds. and parses the cache file on each following run.
Test the script using: zabbix_get -s 10.148.0.3 -p 10050 -k "epmmm.mysql.check[zabbixmysql,10.148.0.3,3306,check]"
The script need zabbix_sender and Python Running Environment
The default monitor mysql port is 3306, if need to monitor other port, you need to add the Macros:{$MYSQL_PORT}=xxxx on the monitor Host
Remember to change the USERNAME PASSWORD ZABBIXSERVER for your's.
Authors: earl86

using:

