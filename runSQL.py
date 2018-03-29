import sys
import os
import threading
from server_functions import *
from client_functions import *
sys.path.append(os.path.abspath(os.path.join('./antlr')))
from antlr import parse_sql
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
        cat_node = {'url': cfg['catalog.hostname'], 'tName': None, 'loop': True}
        cluster_cp = do_connect(cat_node, clustercfg, None, 'parse_cat_db')
        tables = parse_sql.parse_sql_table_name(readFile(ddlfile))
        local_node = {'url': cfg['localnode.hostname'], 'tName': None, 'loop': True}
        local_node['tables'] = tables
        local_node['cluster_cp'] = cluster_cp
        local_node['ddlfile'] = ddlfile
        returnVal = []
        do_connect(local_node, ddlfile, returnVal, 'runLocalNode')
        for returnData in returnVal[0]['data']:
            data_output = ''
            for i in range (len(returnData)):
                data_output += str(returnData[i]) + ' '
            print(data_output)
        for nodes in returnVal[0]['nodes']:
            print('[' + nodes + ']:', returnVal[0]['ddlfile'], returnVal[0]['status'])

        """
        #loop through all the nodes
        returnVal = []
        threads = [None] * numnodes
        for i in range(numnodes):
             threads[i] = threading.Thread(target=do_connect, args=(cluster_cp[i],ddlfile, returnVal, 'runSql'))
             threads[i].start()
        for i in range(numnodes):
            threads[i].join()
        for value in returnVal:
            print('[' + value['url'] + ']:', value['ddlfile'], value['status'])
        """
if __name__ == '__main__':
    main()
