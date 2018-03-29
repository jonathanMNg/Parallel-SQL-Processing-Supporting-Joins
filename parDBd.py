import socket
from socket import error as socket_error
import sys
from client_functions import *
from server_functions import *
import json, pickle
from cluster_server import Cluster_Server
"""
function: init()
parameter: None
return: none
This function will get the value for clustercfg and ddlfile
then declare them as global values
"""
def init():
    global host
    global port
    host = sys.argv[1]
    port = int(sys.argv[2])
"""
function: create update_catalog()
parameter: (string) cfg_filename, (array) tableNames, (int) nodeID
return: (hash) response: status of the catalog
This function execute the sql statement to update the catalog table
and return a message says if the catalog is updated
"""
def init_catalog(cfg_cat, tNames, node):
    nodeid = int(node)
    cfg = parse_config(cfg_cat)
    cat_hostname = cfg['catalog.hostname']
    cat_driver = cfg['catalog.driver']
    cat_cfg = parseUrl(cat_hostname)
    nodedriver = cfg['node%d.driver'%nodeid]
    nodeurl = cfg['node%d.hostname'%nodeid]
    response = {}
    #query to create table if not exists
    sql_table_query = """CREATE TABLE IF NOT EXISTS
                    dtables(tname char(32),
                    nodedriver char(64),
                    nodeurl char(128),
                    nodeuser char(16),
                    nodepasswd char(16),
                    partmtd int,
                    nodeid int,
                    partcol char(32),
                    partparam1 char(32),
                    partparam2 char(32));"""
    cat_db_conn = create_connection(cat_cfg['db'])
    if cat_db_conn is not None:
        create_table(cat_db_conn, sql_table_query)
        #create table if it not yet exists
        for tName in tNames:
            sql_update_query = """INSERT INTO dtables(
                                tname, nodedriver, nodeurl, nodeuser,
                                nodepasswd, partmtd, nodeid, partcol,
                                partparam1, partparam2)
                                SELECT '%s', '%s', '%s', NULL, NULL, NULL, %d,
                                NULL, NULL, NULL
                                WHERE NOT EXISTS (
                                SELECT 1 FROM dtables
                                WHERE tname = '%s'
                                AND nodeid = %d);
                                """ %(tName, nodedriver, nodeurl, nodeid, tName, nodeid)
            response = execute_sql(cat_db_conn, sql_update_query, 'catalog')
        return response
    else:
        print("Error! cannot create the database connection.")
def getSelectedColData(node):
    cp = parseUrl(node['url'])
    db_conn = create_connection(cp['db'])
    c = db_conn.cursor()
    c.execute("PRAGMA table_info('{tNames}') ;".format(tNames=node['tNames']))
    selColIndex = 0
    for row in c.fetchall():
        #location the position of selected column
        colName = row[1]
        if(colName == node['partcol']):
            #get position of selected column
            selColIndex = int(row[0])
            break
    #get the total columns number in the table
    c.execute("PRAGMA table_info('{tNames}') ;".format(tNames=node['tNames']))
    numCol = len(c.fetchall())
    return selColIndex, numCol
"""
function: create update_catalog_csv()
parameter: (string) catalog's hostname: in url-form
            (array) cat_nodes: array of node stored in the catalog
return: (hash) response
This function get info about the nodes in the catalog based on
the array passed into it. Then it will update info about the node (partition...)
based on the nodeid and the tablename
"""
def update_catalog_csv(cat_hostname, cat_nodes):
    cat_cp = parseUrl(cat_hostname)
    cat_conn = create_connection(cat_cp['db'])
    response = {}
    if cat_conn is not None:
        try:
            for node in cat_nodes:
                sql_update_query = """UPDATE dtables SET
                                    tname = '{tname}',
                                    nodedriver = '{nodedriver}',
                                    nodeurl =  '{nodeurl}',
                                    nodeuser = NULL,
                                    nodepasswd = NULL,
                                    partmtd = {partmtd},
                                    partcol = '{partcol}',
                                    partparam1 = '{partparam1}',
                                    partparam2 = '{partparam2}'
                                    WHERE nodeid = {nodeid} AND tName = '{tname}';
                                    """ .format(tname=node['tNames'], \
                                                nodedriver=node['driver'], \
                                                nodeurl=node['url'], \
                                                partmtd = node['partmtd'], \
                                                nodeid=node['id'], \
                                                partcol=node['partcol'], \
                                                partparam1=node['partparam1'], \
                                                partparam2=node['partparam2'])
                c = cat_conn.cursor()
                c.execute (sql_update_query)
            cat_conn.commit()
            response['status'] = "catalog updated."
            return response
        except Error as e:
            response = {}
            response['status'] = 'failed.'
            print (e)
            return response
"""
function: main()
parameter: none
return: none
Main function of the program
"""
def Main():
    if len(sys.argv) < 3:
        print("Error: You didn't enter enough arguments!")
        print("Usage: python3 parDBd.py 'host/ip' 'port'")
        sys.exit()
    else:
        init()
        node2 = Cluster_Server(host, port)
        node2.connect()
        while True:
            #receive type of pc
            node2.listen()
            data_pc_type = node2.recvMessage()
            node2.sendMessage(str("received data_pc_type"))
            data_node = node2.recvData()
            if (data_pc_type == "catalog"):
                #do something with catalog database
                #parse data from cfgFile
                cfgFile = data_node['clustercfg']
                cfg = parse_config(cfgFile)
                numnodes = int(cfg['numnodes'])
                """
                For each node
                    parse the config from that node
                    connect to that node's database
                    execute SQL file to show tables
                    store all the table name into tNames[] array
                    run update_catalog() and store the output in data_cat variable
                    send the ouput to client
                """
                for node in range(1, numnodes + 1):
                    cp = parseUrl(cfg['node%d.hostname' % node])
                    db_conn = create_connection(cp['db'])
                    c = db_conn.cursor()
                    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tNames = []
                    for row in c.fetchall():
                        tNames.append(row[0])
                    response = init_catalog(cfgFile, tNames, node)
                break
            elif (data_pc_type == "runLocalNode"):
                response = {}
                cp = parseUrl(data_node['url'])
                cluster_cp = data_node['cluster_cp']
                ddlfile = data_node['ddlfile']
                numnodes =  count_db_nodes(cluster_cp)
                threads = [None] * numnodes
                #get table name
                tables = data_node['tables']
                returnVal = {}
                join_nodes = []
                for table in tables:
                    returnVal[table] = {}
                    for i in range(numnodes):
                        if(cluster_cp[i]['tNames'] == table):
                            join_nodes.append(cluster_cp[i]['url'])
                        cluster_cp[i]['tableName'] = table
                        cluster_cp[i]['loop'] = True
                        threads[i] = threading.Thread(target=runSQL, args=(cluster_cp[i],returnVal[table],))
                        threads[i].start()
                    for i in range(numnodes):
                        threads[i].join()
                for i in range(numnodes):
                    kill_runSQLSocket(cluster_cp[i])
                db_conn = create_connection(cp['db'])
                c = db_conn.cursor()
                for table in returnVal:
                    tableData = returnVal[table]
                    create_table_sql = "{create_table_sql};".format(create_table_sql=tableData['schema'])
                    create_temp_table_sql = create_table_sql.replace("TABLE", "TEMP TABLE")
                    c.execute(create_temp_table_sql)
                    for row in tableData['row']:
                        insert_sql = "INSERT INTO {table_name} VALUES {row};".format(table_name=table,row=row)
                        c.execute(insert_sql)
                response = execute_sql(db_conn, readFile(ddlfile), 'runSQL', None)
                response['returnVal'] = join_nodes
                break
            elif (data_pc_type == "catalog_csv"):
                cp = data_node['url']
                cat_data = data_node['data']
                response = update_catalog_csv(cp, cat_data)
                break
            elif (data_pc_type == "node"):
                cp = parseUrl(data_node['url'])
                data_ddlFile = data_node['ddlfile']
                db_conn = create_connection(cp['db'])
                if db_conn is not None:
                    #execute statements from sqlFile
                    sqlFile = readFile(data_ddlFile)
                    response = execute_sql(db_conn, sqlFile, 'node')
                break
            elif (data_pc_type == "runSQL"):
                cp = parseUrl(data_node['url'])
                #sql_conn = create_connection(cp['db'])
                response = {}
                if(data_node['loop']):
                    cp = parseUrl(data_node['url'])
                    runSQL_conn = create_connection(cp['db'])
                    c = runSQL_conn.cursor()
                    isTableExist = "SELECT sql FROM sqlite_master WHERE name='{table_name}';".format(table_name=data_node['tableName'])
                    c.execute(isTableExist)
                    #if the table is exist
                    table_cursor = c.fetchall()
                    if(len(table_cursor) > 0):
                        select_all = "SELECT * FROM {table_name}".format(table_name=data_node['tableName'])
                        c.execute(select_all)
                        rows = c.fetchall()
                        totalRow = len(rows)
                        tableData = {'isExists': True, 'totalRow': totalRow, 'schema': table_cursor[0][0]}
                        node2.sendData(tableData)
                        for row in rows:
                            node2.listen()
                            node2.sendData(row)
                    else:
                        tableData = {'isExists': False}
                        node2.sendData(tableData)
                else:
                    break
            elif (data_pc_type == "csv"):
                cp = parseUrl(data_node['url'])
                csv_delimiter = data_node['delimiter']
                csv_conn = create_connection(cp['db'])
                response = loadCSV(data_node, csv_conn, csv_delimiter)
                break
            elif (data_pc_type == "parse_cat_db"):
                cp = parseUrl(data_node['url'])
                tName = data_node['tName']
                response = parse_cat_db(cp['db'], tName)
                if(data_node['loop']):
                    node2.sendData(response)
                else:
                    break
            elif (data_pc_type == "multi_thread"):
                if(data_node['sql_insert'] != None):
                    cp = parseUrl(data_node['url'])
                    csv_delimiter = data_node['delimiter']
                    csv_conn = create_connection(cp['db'])
                    response = multi_threadloadCSV(data_node, csv_conn, csv_delimiter)
                    if(data_node['loop']):
                        node2.sendData(response)
                    else:
                        break
                else:
                    response = {'status': 'finish'}
                    break
            #Part4X-MultiThreaded
            elif (data_pc_type == "get_partition_data"):
                selColIndex, numCol = getSelectedColData(data_node)
                response = {'selectedColIndex': selColIndex, 'numCol': numCol}
                if(data_node['loop']):
                    node2.sendData(response)
                else:
                    break
            else:
                break
        node2.sendData(response)
        node2.close()

if __name__ == '__main__':
    Main()
