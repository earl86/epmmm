#!/bin/env python
# python3 zabbix-create_screen_new.py -g "group_A" "group_B" -G "graph_A" "graph_B" -c Screen_columns -n 'Screen_name'
#pip3 install requests

import json
import urllib.request
import argparse
import re
 
re_digits = re.compile(r'(\d+)')
 
def emb_numbers(s):
    pieces=re_digits.split(s)
    pieces[1::2]=map(int,pieces[1::2])
    return pieces
 
def sort_strings_with_emb_numbers2(alist):
    return sorted(alist, key=emb_numbers)
 
def requestjson(url, values):
    header = {"Content-Type": "application/json"}
    data = json.dumps(values).encode('utf-8')
    req = urllib.request.Request(url, headers=header)
    res = urllib.request.urlopen(req, data=data)
    output = json.loads(res.read().decode('utf-8'))
    return output
 
 
def authenticate(url, username, password):
    values = {'jsonrpc': '2.0',
              'method': 'user.login',
              'params': {
                  'user': username,
                  'password': password
              },
              'id': '0'
    }
    output = requestjson(url, values)
    return output['result']
 
def gethosts(groupname, url, auth):
    host_list = {}
    for gname in groupname:
        values = {'jsonrpc': '2.0',
                  'method': 'hostgroup.get',
                  'params': {
                      'output': 'extend',
                      'filter': {'name': gname},
                      'selectHosts': ['host']
                  },
                  'auth': auth,
                  'id': '2'
        }
        output = requestjson(url, values)
        for host in output['result'][0]['hosts']:
            host_list[host['host']]=(host['hostid'])
 
    #return host_list
    hosts_sort = []
    for host in sort_strings_with_emb_numbers2(host_list.keys()):
        hosts_sort.append(host_list[host])
    return  hosts_sort
 
def getgraphs(host_list, name_list, url, auth, columns, graphtype=0, dynamic=0):
    if (graphtype == 0):
        selecttype = ['graphid']
        select = 'selectGraphs'
    if (graphtype == 1):
        selecttype = ['itemid', 'value_type']
        select = 'selectItems'
 
    graphs = []
    for host in host_list:
        for gname in name_list:
            values = ({'jsonrpc': '2.0',
                       'method': 'graph.get',
                       'params': {
                           select: [selecttype, 'name'],
                           'output': ['graphid', 'name'],
                           'hostids': host,
                           'filter': {'name': gname},
                           'sortfield': 'name'
                       },
                       'auth': auth,
                       'id': '3'
                       })
            output = requestjson(url, values)
            bb = sorted(output['result'])
            if (graphtype == 0):
                for i in bb:
                    graphs.append(i['graphid'])
            if (graphtype == 1):
                for i in bb:
                    if int(i['value_type']) in (0, 3):
                        graphs.append(i['itemid'])

    graph_list = []
    x = 0
    y = 0
    if columns == 2:
        width = 750
        height = 150
    elif columns == 3:
        width = 480
        height = 120
    else:
        width = 390
        height = 100
    for graph in graphs:
        graph_list.append({
            'resourcetype': graphtype,
            'resourceid': graph,
            'width': width,
            'height': height,
            'x': str(x),
            'y': str(y),
            'colspan': '1',
            'rowspan': '1',
        })
        x += 1
        if x == int(columns):
            x = 0
            y += 1
    return graph_list
 
def screencreate(url, auth, screen_name, graphids, columns):
    columns = int(columns)
    if len(graphids) % columns == 0:
        vsize = len(graphids) / columns
    else:
        vsize = int(len(graphids) / columns) + 1
 
    values = {'jsonrpc': '2.0',
              'method': 'screen.create',
              'params': [{
                  'name': screen_name,
                  'hsize': columns,
                  'vsize': vsize,
                  'screenitems': []
              }],
              'auth': auth,
              'id': 2
              }
    for i in graphids:
        values['params'][0]['screenitems'].append(i)
    output = requestjson(url, values)
 
def main():
    ZABBIX_URL = 'http://192.168.1.100:8081'
    ZABBIX_USERNAME = 'xxx'
    ZABBIX_PASSWORD = 'xxx'
    url = "{}/api_jsonrpc.php".format(ZABBIX_URL)
    auth = authenticate(url, ZABBIX_USERNAME, ZABBIX_PASSWORD)
    host_list = gethosts(groupname, url, auth)
    graph_ids = getgraphs(host_list, graphname, url, auth, columns)
    screencreate(url, auth, screen_name, graph_ids, columns)
 
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', dest='groupname', nargs='+', metavar='groupname', type=str, help='which host groups you want to select')
    parser.add_argument('-G', dest='graphname', nargs='+', metavar='graphname', type=str, help='which graphs you want to select')
    parser.add_argument('-c', dest='columns', metavar='columns', type=int, help='the screen columns')
    parser.add_argument('-n', dest='screen_name', metavar='screen_name', type=str, help='the screen name')

    args = parser.parse_args()
    groupname = args.groupname
    graphname = args.graphname
    columns = args.columns
    screen_name = args.screen_name
    #print(groupname,graphname,columns,screen_name)
    main()

