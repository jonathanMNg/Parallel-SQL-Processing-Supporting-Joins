import sys
import threading
from server_functions import *
from client_functions import *
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
        cat_node = {'url': cfg['catalog.hostname'], 'tName': cfg['tablename'], 'loop': False}
        cluster_cp = do_connect(cat_node, clustercfg, None, 'parse_cat_db')
        #get numnodes
        numnodes =  count_db_nodes(cluster_cp)
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

if __name__ == '__main__':
    main()
