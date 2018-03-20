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
        #get numnodes
        numnodes =  count_db_nodes(cluster_cp)
        threads = [None] * numnodes
        #get table name
        tables = parse_sql.parse_sql_table_name(readFile(ddlfile))
        returnVal = {}
        for table in tables:
            returnVal[table] = {}
            for i in range(numnodes):
                cluster_cp[i]['tableName'] = table
                cluster_cp[i]['loop'] = True
                threads[i] = threading.Thread(target=runSQL, args=(cluster_cp[i],returnVal[table],))
                threads[i].start()
            for i in range(numnodes):
                threads[i].join()
        for i in range(numnodes):
            kill_runSQLSocket(cluster_cp[i])
        db_conn = create_connection(':memory:')
        c = db_conn.cursor()
        for table in returnVal:
            tableData = returnVal[table]
            create_table_sql = "{create_table_sql};".format(create_table_sql=tableData['schema'])
            c.execute(create_table_sql)
            for row in tableData['row']:
                insert_sql = "INSERT INTO {table_name} VALUES {row};".format(table_name=table,row=row)
                insert_sql = insert_sql.replace("'", '')
                c.execute(insert_sql)

        c.execute(readFile(ddlfile))
        print(c.fetchall())

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
