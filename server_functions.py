import csv
from sqlite3 import Error
import sqlite3
"""
function: create_connection()
parameter: (string) database_file
return: Connection object or None
This function creates a database connection to the SQLite database
specified by database_file
"""
def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None
"""
function: execute_sql()
parameter: (connection object) conn, (string) sqlStatement, (hash) pc_config,
            (string) ddlfile
return: None
This function execute the sql statement
"""
def execute_sql(conn, sqlFile, cp_type, sql_list=''):
    try:
        c = conn.cursor()
        response = {}
        if(cp_type == 'catalog'):
            c.execute(sqlFile)
            conn.commit()
            response['status'] = 'catalog updated.'
        elif(cp_type == 'runSQL'):
            c.execute(sqlFile)
            conn.commit()
            response['status'] = 'success.'
            response['data'] = c.fetchall()
        elif(cp_type == 'csv'):
            for sql_ in sql_list:
                c.execute(sqlFile, sql_)
            conn.commit()
            row_count = conn.total_changes
            response['status'] = "{num_row} rows inserted." .format(num_row=row_count)
        elif(cp_type == 'csv_multi_thread'):
            c.execute(sqlFile, sql_list)
            conn.commit()
            response['status'] = 'success.'
        else: #if it's node
            c.execute(sqlFile)
            conn.commit()
            response['status'] = 'success.'
        return response
    except Error as e:
        response = {}
        response['status'] = 'failed.'
        print (e)
        return response

"""
function: create_table()
parameter: (connection object) conn, (string) sqlStatement
return: None
This function execute the sql statement to create the table
"""
def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

"""
function: parseCSV()
parameter: (string) csvfile, (char) delimiter: the csv's divider (default value is ',')
return: (array) each element represent a line in the csv file
This function parse the csvfile in to an array
"""
def parseCSV(filename, csv_delimiter = ','):
    csvData = []
    with open(filename, newline='' ) as f:
        reader = csv.reader(f, delimiter=csv_delimiter)
        for row in reader:
            if(row[-1] == ''):
                row = row[:-1]
            csvData.append(csv_delimiter.join(row))
    return csvData

"""
function: loadCSV()
parameter: (hash) node, (connection obj) db_conn, (char) delimiter: the csv's divider (default value is ',')
return: (hash) response: status of the sql
This will load the csv to the database based on the partition in the cluster configuration
"""
def loadCSV(node, db_conn, delimiter=','):
    #parse data from csvfile
    csvData = parseCSV(node['csvfile'], delimiter)
    #get selected column from the first line of csv file
    csv = csvData[0];
    csv_row = []
    #init number of columns in table
    numCol = 0
    #init selected column value
    selColIndex = 0

    c = db_conn.cursor()
    """
    Select all table info, to get all the columns' name
    Iterate through each name until it matches the config column name
    Set the selected column index selColIndex to the position of the column
    """
    c.execute("PRAGMA table_info('{tNames}') ;".format(tNames=node['tNames']))
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
                """ .format(tNames=node['tNames'], \
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
        if(node['partmtd'] == 0):
            csv_row.append(csv)
        elif(node['partmtd'] == 1):
            #range partition
            pmin = float(node['partparam1'])
            pmax = float(node['partparam2'])
            selColVal = float(csv[selColIndex])
            if(selColVal >= pmin and selColVal < pmax):
                csv_row.append(csv)
        elif(node['partmtd'] == 2):
            #hash partition
            param1 = int(node['partparam1'])
            node_id = int(node['id'])
            selColVal = float(csv[selColIndex])
            if(node_id == int(selColVal % param1) + 1):
                csv_row.append(csv)
        else:
            pass
    response = execute_sql(db_conn, load_sql, 'csv', csv_row)
    return response
"""
function: readFile()
parameter: (string) filename: name of ddlfile
return: (hash) data: string of sql from the ddlfile
This function read a ddlfile and return the line from the ddlfile
"""
def readFile(filename):
    fd = open(filename, 'r')
    data = fd.read()
    fd.close()
    return data

"""
function: parse_cat_db()
parameter: (string) db_name: name of databse, (string) tName: table need to parse
return: (array) data: all the node in db_name with table name is tName
This function parse the data in the catalog database and return node with the
tablename is tName
"""
def parse_cat_db(db_name, tName):
    cat_conn = create_connection(db_name)
    if cat_conn is not None:
        c = cat_conn.cursor()
        if(tName is not None):
            c.execute("SELECT * FROM dtables WHERE tname='{tName}'".format(tName=tName))
        else:
            c.execute("SELECT * FROM dtables")
        tData = []
        for row in c.fetchall():
            node = {}
            node['tNames'] = row[0]
            node['driver'] = row[1]
            node['url'] = row[2]
            node['user'] = row[3]
            node['passwd'] = row[4]
            node['partmtd'] = row[5]
            node['id'] = row[6]
            node['partcol'] = row[7]
            node['partparam1'] = row[8]
            node['partparam2'] = row[9]
            tData.append(node)
    return tData
"""
function: multi_threadloadCSV()
parameter: (hash) node, (connection obj) db_conn, (char) delimiter: the csv's divider (default value is ',')
return: (hash) response: status of the sql
This will load the csv to the database based on the partition in the cluster configuration
"""
def multi_threadloadCSV(node, db_conn, delimiter=','):
    csv_row = node['sql_insert']
    c = db_conn.cursor()
    #get the total columns number in the table
    c.execute("PRAGMA table_info('{tNames}') ;".format(tNames=node['tNames']))
    numCol = len(c.fetchall())
    #generate list with question marks
    sql_list = '('
    for i in range(1, numCol):
        sql_list += '?,'
    sql_list += '?)'
    #generate sql statement
    load_sql = """INSERT INTO {tNames}
                VALUES {sql_list};
                """ .format(tNames=node['tNames'], \
                sql_list=sql_list)

    response = execute_sql(db_conn, load_sql, 'csv_multi_thread', csv_row)
    return response
