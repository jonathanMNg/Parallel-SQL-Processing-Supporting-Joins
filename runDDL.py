import sys
import sqlite3
from sqlite3 import Error
import time
import threading
from client_functions import parseUrl
from client_functions import parse_config
from client_functions import do_connect
import socket
from socket import error as socket_error
import json, pickle
"""
function: init()
parameter: None
return: none
This function will get the value for clustercfg and ddlfile
then declare them as global values
"""
def init():
    global clustercfg
    global ddlfile
    clustercfg = sys.argv[1]
    ddlfile = sys.argv[2]

"""
function: main()
parameter: none
return: none
Main function of the program
"""
def main():
    if len(sys.argv) < 3:
        print("Error: You didn't enter enough arguments!")
        print("Usage: python3 runDDL.py ./cfgfile ./ddlfile")
        sys.exit()
    else:
        init()
        cfg = parse_config(clustercfg)
        #get numnodes
        numnodes = int(cfg['numnodes'])
        #loop through all the nodes
        returnVal = []
        threads = [None] * numnodes
        for i in range(numnodes):
            cp = {}
            cp['url'] = cfg['node%d.hostname' % (i+1)]
            threads[i] = threading.Thread(target=do_connect, args=(cp,ddlfile, returnVal, 'node'))
            threads[i].start()
        for i in range(numnodes):
            threads[i].join()

        # updata catalog table
        catalog_cp = {}
        catalog_cp['url'] = cfg['catalog.hostname']
        do_connect(catalog_cp, clustercfg, returnVal,'catalog')
        for value in returnVal:
            print('[' + value['url'] + ']:', value['ddlfile'], value['status'])

if __name__ == '__main__':
    main()
