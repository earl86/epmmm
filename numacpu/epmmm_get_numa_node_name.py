#!/usr/bin/env python
#pip3 install strip_ansi
#pip3 install pexpect

from strip_ansi import strip_ansi
import json
import pexpect


def main():
    cmd = 'top -n 2'
    child = pexpect.spawn(cmd, timeout=2, encoding='utf-8',env = {"TERM": "dumb"})
    child.send('2')
    info=child.read()
    a=info.split('\n')
    numacpunodes = []
    for line in a:
        if (line.find("%Node") == 0):
            #print(strip_ansi(line))
            newline=strip_ansi(line).split()
            numacpunodes.append(strip_ansi(newline[0]).strip('%'))

    data = [{"{#NUMACPUNODENAME}": cpunode} for cpunode in numacpunodes]
    print(json.dumps({"data": data}, indent=4))


if __name__ == '__main__':
    main()
