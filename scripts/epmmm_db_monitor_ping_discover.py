#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import json


def get_servicename(hostname):
    servicedict = {
        'cw_memcached_1_1_1': ['cw_memcached_1_1_2', 0], 'cw_memcached_1_1_2': ['cw_memcached_1_1_1', 0],
        'cw_memcached_1_2_1': ['cw_memcached_1_2_2', 0], 'cw_memcached_1_2_2': ['cw_memcached_1_2_1', 0],

        'em_memcached_6_1_1': ['em_memcached_6_1_2', 0], 'em_memcached_6_1_2': ['em_memcached_6_1_1', 0],
        'em_memcached_6_2_1': ['em_memcached_6_2_2', 0], 'em_memcached_6_2_2': ['em_memcached_6_2_1', 0],
        'em_memcached_6_3_1': ['em_memcached_6_3_2', 0], 'em_memcached_6_3_2': ['em_memcached_6_3_1', 0],
        'em_memcached_6_4_1': ['em_memcached_6_4_2', 0], 'em_memcached_6_4_2': ['em_memcached_6_4_1', 0],
        'em_memcached_6_5_1': ['em_memcached_6_5_2', 0], 'em_memcached_6_5_2': ['em_memcached_6_5_1', 0],
        'em_memcached_6_5_1': ['em_memcached_6_6_2', 0], 'em_memcached_6_6_2': ['em_memcached_6_5_1', 0],
        'em_memcached_6_7_1': ['em_memcached_6_7_2', 0], 'em_memcached_6_7_2': ['em_memcached_6_7_1', 0],
        'em_memcached_6_8_1': ['em_memcached_6_8_2', 0], 'em_memcached_6_8_2': ['em_memcached_6_8_1', 0],

        'em_memcached_7_1_1': ['em_memcached_7_1_2', 0], 'em_memcached_7_1_2': ['em_memcached_7_1_1', 0],
        'em_memcached_7_2_1': ['em_memcached_7_2_2', 0], 'em_memcached_7_2_2': ['em_memcached_7_2_1', 0],
        'em_memcached_7_3_1': ['em_memcached_7_3_2', 0], 'em_memcached_7_3_2': ['em_memcached_7_3_1', 0],
        'em_memcached_7_4_1': ['em_memcached_7_4_2', 0], 'em_memcached_7_4_2': ['em_memcached_7_4_1', 0],

        'em_memcached_8_1_1': ['em_memcached_8_1_2', 0], 'em_memcached_8_1_2': ['em_memcached_8_1_1', 0],
        'em_memcached_8_2_1': ['em_memcached_8_2_2', 0], 'em_memcached_8_2_2': ['em_memcached_8_2_1', 0],
        'em_memcached_8_3_1': ['em_memcached_8_3_2', 0], 'em_memcached_8_3_2': ['em_memcached_8_3_1', 0],
        'em_memcached_8_4_1': ['em_memcached_8_4_2', 0], 'em_memcached_8_4_2': ['em_memcached_8_4_1', 0],
        'esmysql1':['cmysql60', 1],
        'esmysql2':['cmysql44', 1],
        'esmysql3':['cmysql63', 1],
        'esmysql4':['cmysql66', 1],
        'esmysql5':['cmysql70', 1],
        'esmysql6':['cmysql51', 1],
        'esmysql7':['cmysql54', 1],
        'esmysql8':['cmysql57', 1],
        'esmysql9':['cmysql37', 1],
        }

    try:
        return servicedict[hostname]
    except Exception:
        return None

if __name__ == "__main__":
    hostname = sys.argv[1]
    servicename = get_servicename(hostname)[0]
    if servicename:
        data = [{"{#INSTANCEIP}": servicename}]
        print(json.dumps({"data": data}, indent=4))
