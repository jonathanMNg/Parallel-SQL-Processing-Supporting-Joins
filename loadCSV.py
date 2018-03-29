import sys
import socket
import json
import pickle
from socket import error as socket_error
from client_functions import *
from server_functions import *
"""
function: init()
parameter: None
return: none
This function will get the value for clustercfg and ddlfile
then declare them as global values
"""
def init():
    global clustercfg
    global csvfile
    clustercfg = sys.argv[1]
    csvfile = sys.argv[2]
"""
function: get_partmtd()
parameter: (string) partmtd_name: name of partition method
return: (int) partmtd: a number's version of the partition method name
This function will translate the partition method as a string
to an integer
"""
def get_partmtd(partmtd_name):
    if(partmtd_name == "notpartition"):
        return 0
    elif(partmtd_name == "range"):
        return 1
    elif(partmtd_name == "hash"):
        return 2
    else:
        return -1
"""
function: main()
parameter: none
return: none
Main function of the program
"""
def main():
    init()
    cfg = parse_config(clustercfg)
    cat_db_name = parseUrl(cfg['catalog.hostname'])['db']
    cat_node = {'url': cfg['catalog.hostname'], 'tName': cfg['tablename'].upper(), 'loop': True}
    cat_db = do_connect(cat_node, clustercfg, None, 'parse_cat_db')
    partmtd = get_partmtd(cfg['partition.method'])
    if(partmtd == 2):
        numnodes = int(cfg['partition.param1'])
    else:
        numnodes = int(cfg['numnodes'])
    numnodes_cat_db = count_db_nodes(cat_db)
    if(numnodes == numnodes_cat_db):
        #identify partition method
        returnVal = []
        for i in range(numnodes):
            #check if the table is already partitioned, if it's not then partition the table
            if(cat_db[i]['partmtd'] == None or cat_db[i]['partmtd'] == 0 or cat_db[i]['partmtd'] == partmtd):
                cat_db[i]['partmtd'] = partmtd
            else:
                print("Error: the table is already partitioned with a different method.")
                sys.exit()
            cat_db[i]['tNames'] = cfg['tablename']
            cat_db[i]['delimiter'] = cfg['delimiter']
            cat_db[i]['csvfile'] = csvfile
            if (partmtd == 1):
                cat_db[i]['partcol'] = cfg['partition.column']
                cat_db[i]['partparam1'] = cfg['partition.node%d.param1' % (i + 1)]
                cat_db[i]['partparam2'] = cfg['partition.node%d.param2' % (i + 1)]
            elif (partmtd == 2):
                cat_db[i]['partcol'] = cfg['partition.column']
                cat_db[i]['partparam1'] = cfg['partition.param1']
            else:
                pass
            do_connect(cat_db[i], csvfile, returnVal, 'csv')
        #update catalog
        cat_cp = {}
        cat_cp['url'] = cfg['catalog.hostname']
        cat_cp['data'] = cat_db
        do_connect(cat_cp, clustercfg, returnVal, 'catalog_csv' )
        for value in returnVal:
            print('[' + value['url'] + ']:', value['ddlfile'], value['status'])
    else:
        print("Error: Number of nodes in catalog and numnodes in {} doesn't match"  \
            .format( clustercfg))

if __name__ == '__main__':
    main()
