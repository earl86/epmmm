#!/usr/bin/python
import os
import re
import json


if __name__ == "__main__":
    disk_re = "sd[a-z]$|sd[a-z][a-z]$|md[0-9]+$|nvme[0-9]+n[0-9]$"
    disk_full_list=os.listdir("/sys/class/block")
    #print(disk_full_list)
    devices=[]
    for disk in disk_full_list:
        disk_name = re.findall(disk_re,disk)
        if len(disk_name)>0:
            devices.append(disk_name[0])
    #print(devices)
    data = [{"{#DEVICENAME}": device} for device in devices]
    print(json.dumps({"data": data}, indent=4))
