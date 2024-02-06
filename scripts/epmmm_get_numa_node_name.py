#!/usr/bin/env python

#pip3 install json

from subprocess import Popen
from subprocess import PIPE
import json

def main():
    try:
        numacpunodes = []
        cmd='/usr/bin/numactl -s'
        dataStr=Popen(args=cmd, stdout=PIPE, shell=True).stdout.read().decode()
        for info in dataStr.split('\n'):
            if info.startswith('nodebind'):
                nodeinfo = info.split()
                for node in nodeinfo[1:]:
                    numacpunodes.append(node)

                data = [{"{#NUMACPUNODENAME}": 'Node'+cpunode} for cpunode in numacpunodes]
                print(json.dumps({"data": data}, indent=4))
    except Exception:
        pass

if __name__ == '__main__':
    main()
