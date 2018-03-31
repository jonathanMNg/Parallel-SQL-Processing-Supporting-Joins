import sys
import os
import threading
from queue import Queue
from threading import Thread
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

PARTMTD_NOTPARTITION = 0
PARTMTD_RANGE = 1
PARTMTD_HASH = 2
"""
function: processQueues()
parameter: (queue) q, (cluster machine data) node
return: none
This function will connect to the server machine and send
data in the queue until none is left
"""
def processQueues(q,node):
    while True:
        node['loop'] = True
        node['sql_insert'] = q.get()
        do_connect(node, 0, 0, "multi_thread")
        q.task_done()
"""
function get_response()
parameter: (cluster machine data) node
return: none
This function will send the signal to the cluster machine
to break the connection
"""
def end_queue(node):
    node['sql_insert'] = None
    node['loop'] = False
    do_connect(node, 0, 0, "multi_thread")

"""
function: get_partmtd()
parameter: (string) partmtd_name: name of partition method
return: (int) partmtd: a number's version of the partition method name
This function will translate the partition method as a string
to an integer
"""
def get_partmtd(partmtd_name):
    if(partmtd_name == "notpartition"):
        return PARTMTD_NOTPARTITION
    elif(partmtd_name == "range"):
        return PARTMTD_RANGE
    elif(partmtd_name == "hash"):
        return PARTMTD_HASH
    else:
        return -1
"""
function: isValidPartition()
parameter: (string) currentDB_partmtd, string clustercfg_partmtd
return: (bool)
This function will check if the partition method in the cfg, if it's not partition
or same as the current partition in the catalog database, it returns true, else return false
"""
def isValidPartition(currentDB_partmtd, clustercfg_partmtd):
    if(currentDB_partmtd == PARTMTD_NOTPARTITION or currentDB_partmtd == clustercfg_partmtd \
        or currentDB_partmtd == None):
        return True
    else:
        return False

"""
function: loadCSV()
parameter: (hash) node, (connection obj) db_conn, (char) delimiter: the csv's divider (default value is ',')
return: (hash) response: status of the sql
This will load the csv to the database based on the partition in the cluster configuration
"""
def loadDataToQueues(queues,partitionData, cat_db):
    row_changes = [0] * len(queues)
    #parse data from csvfile
    delimiter = partitionData['delimiter']
    csvData = parseCSV(partitionData['csvfile'], delimiter)
    #get selected column from the first line of csv file
    csv = csvData[0];
    csv_row = []
    #init number of columns in table
    numCol = partitionData['numCol']
    #init selected column value
    selectedColIndex = partitionData['selectedColIndex']
    """
    To load data into table, the syntax of our sql will be like this:
        INSERT INTO "tName" VALUES (?, ?, ?,.. ?n) where n is the total columns
        in the table
    """
    #generate list with question marks
    sql_list = '('
    for i in range(1, numCol):
        sql_list += '?,'
    sql_list += '?)'
    #generate sql statement
    load_sql = """INSERT INTO {tNames}
                VALUES {sql_list};
                """ .format(tNames=partitionData['tNames'], \
                sql_list=sql_list)
    """
    For each line in the csvfile, it will be split based on the delimiter
    Then, put the data into the partition based on the partition method
    based on clustercfg.
    If the data match with the partition, then it will be append to csv_row[array]
    Then it will be execute in sql to load the data into the selected partition.
    """
    for csv in csvData:
        csv = csv.split(delimiter)
        for i in range(len(cat_db)):
            if(partitionData['partmtd'] == 0):
                #no partition
                queues[i].put(csv)
                row_changes[i] = row_changes[i] + 1
            elif(partitionData['partmtd'] == 1):
                #range partition
                pmin = float(cat_db[i]['partparam1'])
                pmax = float(cat_db[i]['partparam2'])
                selColVal = float(csv[selectedColIndex])
                if(selColVal >= pmin and selColVal < pmax):
                    queues[i].put(csv)
                    row_changes[i] = row_changes[i] + 1
            elif(partitionData['partmtd'] == 2):
                #hash partition
                param1 = int(cat_db[i]['partparam1'])
                node_id = int(cat_db[i]['id'])
                selColVal = float(csv[selectedColIndex])
                if(node_id == int(selColVal % param1) + 1):
                    queues[i].put(csv)
                    row_changes[i] = row_changes[i] + 1
            else:
                pass
            queues[i].join()
    return row_changes

def getDDLFileType(ddlfile):
    splitDDLFile = ddlfile.split('.')
    return splitDDLFile[-1].upper()
def getSQLOperationType(ddlfile):
    splitSqlStatement = readFile(ddlfile).split(' ')
    return splitSqlStatement[0].upper()
def handleSqlSelect(clustercfg, ddlfile):
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
def handleSqlCreate(clustercfg, ddlfile):
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
def handleSqlInsert(clustercfg, ddlfile):
    handleSqlCreate(clustercfg, ddlfile)
def handleSqlDrop(clustercfg, ddlfile):
    handleSqlCreate(clustercfg, ddlfile)
def handleCSV(clustercfg, ddlfile):
    partcol = None

    cfg = parse_config(clustercfg)
    partmtd = get_partmtd(cfg['partition.method'])
    if(partmtd != 0):
        partcol = cfg['partition.column']
    cat_db_name = parseUrl(cfg['catalog.hostname'])['db']
    cat_node = {'url': cfg['catalog.hostname'], 'tName': cfg['tablename'], 'loop': True}
    cat_db = do_connect(cat_node, clustercfg, None, 'parse_cat_db')
    partition_node = {'url': cat_db[0]['url'], 'tNames': cat_db[0]['tNames'], 'partcol': partcol, 'loop': True}
    partition_data = do_connect(partition_node, 0, 0, "get_partition_data")
    partition_data['delimiter'] = cfg['delimiter']
    partition_data['csvfile'] = ddlfile
    partition_data['tNames'] = cfg['tablename']


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
                partition_data['partmtd'] = partmtd
                cat_db[i]['partmtd'] = partmtd
            else:
                print("Error: the table is already partitioned with a different method.")
                sys.exit()

            cat_db[i]['tNames'] = cfg['tablename']
            cat_db[i]['delimiter'] = cfg['delimiter']
            if (partmtd == 1):
                partition_data['partcol'] = cfg['partition.column']
                cat_db[i]['partparam1'] = cfg['partition.node%d.param1' % (i + 1)]
                cat_db[i]['partparam2'] = cfg['partition.node%d.param2' % (i + 1)]
            elif (partmtd == 2):
                partition_data['partcol'] = cfg['partition.column']
                cat_db[i]['partparam1'] = cfg['partition.param1']
            else:
                pass
    queues = []
    threads = []
    for i in range(numnodes):
        queues.append(Queue(maxsize=10))
        threads.append(Thread(target=processQueues, args=(queues[i],cat_db[i],)))
    for i in range(numnodes):
      worker = threads[i]
      worker.setDaemon(True)
      worker.start()
    row_changes = loadDataToQueues(queues, partition_data, cat_db)
    for i in range(numnodes):
        end_queue(cat_db[i])

    returnVal = []
    #update catalog
    cat_cp = {}
    cat_cp['url'] = cfg['catalog.hostname']
    cat_cp['data'] = cat_db
    do_connect(cat_cp, clustercfg, returnVal, 'catalog_csv' )
    for i in range(numnodes):
        print('[' + cat_db[i]['url'] + ']:', ddlfile, row_changes[i], ' rows inserted.')
    for value in returnVal:
        print('[' + value['url'] + ']:', value['ddlfile'], value['status'])
def main():
    if len(sys.argv) < 3:
        print("Error: You didn't enter enough arguments!")
        print("Usage: python3 runDDL.py ./cfgfile ./ddlfile")
        sys.exit()
    else:
        init()
        filetype = getDDLFileType(ddlfile)
        if(filetype == 'SQL'):
            sqlOperation = getSQLOperationType(ddlfile)
            if(sqlOperation == 'SELECT'):
                handleSqlSelect(clustercfg, ddlfile)
            elif(sqlOperation == 'INSERT'):
                handleSqlInsert(clustercfg, ddlfile)
            elif(sqlOperation == 'CREATE'):
                handleSqlCreate(clustercfg, ddlfile)
            elif(sqlOperation == 'DROP'):
                handleSqlDrop(clustercfg, ddlfile)
            else:
                print("Your sql is invalid or the sql operation is not supported")
        elif(filetype == 'CSV'):
            handleCSV(clustercfg, ddlfile)
        else:
            print ("Not a valid file type")
            sys.exit()

if __name__ == '__main__':
    main()
