import json, pickle
import threading
from urllib.parse import urlparse
import socket
from socket import error as socket_error
from cluster_client import Cluster_Client
"""
function: parseUrl()
parameter: (string) hostname
return: (hash) node
This function receives hostname from clustercfg file as a string. Then it will
parse the string into host, port, and databse name that will contains in a node
that will be returned.
"""
def parseUrl(hostname):
    node = {}
    o = urlparse(hostname)
    data = o.path.split('/')
    node['host'] =  o.scheme
    node['port'] = (data[0])
    node['db'] = (data[1])
    return node
"""
function: parse_config()
parameter: (string) filename
return: hash (options)
This function receive the filename of the clustercfg file.
Then it will parse and store the information into a hash.
Users can retrieve the information by calling the variable
from the cfgfile
"""
def parse_config(filename):
    COMMENT_CHAR = '#'
    OPTION_CHAR = '='
    options = {}
    f = open(filename)
    for line in f:
        # First, remove comments:
        if COMMENT_CHAR in line:
            # split on comment char, keep only the part before
            line, comment = line.split(COMMENT_CHAR, 1)
        # Second, find lines with an option=value:
        if OPTION_CHAR in line:
            # split on option char:
            option, value = line.split(OPTION_CHAR, 1)
            # strip spaces:
            option = option.strip()
            value = value.strip()
            # store in dictionary:
            options[option] = value
    f.close()
    return options
"""
function: runSQL()
parameter: (conf) node, (dict) returnVal
return: None
This function receive the config node as parameter, and passed returnVal by reference
It will connect to the server socket and query the ddlfile from the server, then return the result into returnVal and also the status failed or succeed
"""
def runSQL(node, returnVal):
    returnVal['schema'] = None
    returnVal['row'] = []
    mySocket = socket.socket()
    cp = parseUrl(node['url'])
    data_send = node
    try:
        mySocket.connect((cp['host'], int(cp['port']) ))
        data_cp_type = 'runSQL'
        mySocket.send(data_cp_type.encode())
        data_recv = mySocket.recv(1024).decode()
        data_string = pickle.dumps(data_send)
        mySocket.send(data_string)
        tableData = pickle.loads(mySocket.recv(4096))
        if(tableData['isExists']):
            returnVal['schema'] = tableData['schema']
            for i in range (int(tableData['totalRow'])):
                node1 = Cluster_Client(cp['host'], int(cp['port']))
                node1.connect()
                try:
                    row_data = node1.recvData()
                    returnVal['row'].append(row_data)
                except:
                    break
        else:
            pass
        mySocket.close()
    except socket_error as e:
        print ('[' + node['url']+ ']:',e)
"""
function: kill_runSQLSocket()
parameter: (conf) node,
return: None
This function will kill the connection the the socket by sending a signal
to make the socket loop (which run indifinitely) break.
"""
def kill_runSQLSocket(node):
    mySocket = socket.socket()
    cp = parseUrl(node['url'])
    node['loop'] = False
    data_send = node
    try:
        mySocket.connect((cp['host'], int(cp['port']) ))
        data_cp_type = 'runSQL'
        mySocket.send(data_cp_type.encode())
        data_recv = mySocket.recv(1024).decode()
        data_string = pickle.dumps(data_send)
        mySocket.send(data_string)
        mySocket.close()
    except socket_error as e:
        print ('[' + node['url']+ ']:', e)
"""
function: do_connect()
parameter: (hash) node, (string) ddlfile, (array) returnVal, (string) type
return: none
This function receive the information about the cluster pc, and ddlfile name
Then it will connect to the server PC(s) and send the config and data needed
for the server to process.
After a response is received from server, the status and info of the request will be
passed to reference returnVal.
"""
def do_connect(node, filename, returnVal, cp_type):
    cp = parseUrl(node['url'])
    client_node = Cluster_Client(cp['host'], int(cp['port']))
    data_send = node
    returnObj = {}
    returnObj['url'] = node['url']
    if(cp_type in (('node','','csv','multi_thread'))):
        #connect cluster machines
        returnObj['ddlfile'] = filename
        data_send['ddlfile'] = filename

    else:
        #connect to catalog
        returnObj['ddlfile'] = ''
        data_send['clustercfg'] = filename
    try:
        client_node.connect()
        #pc type
        data_cp_type = cp_type
        client_node.sendMessage(data_cp_type)
        #listen from server
        data_recv = client_node.recvMessage()
        #send config info
        client_node.sendData(data_send)
        #receive response (status)
        data_response = client_node.recvData()
        if(cp_type == 'runLocalNode'):
            returnObj['data'] = data_response['data']
            returnObj['nodes'] =data_response['returnVal']
            returnObj['ddlfile'] = node['ddlfile']
        if(cp_type == 'sql'):
            for data in data_response['data']:
                print(data[0], data[1], data[2])
        if(cp_type == 'parse_cat_db' or cp_type == 'get_partition_data' or cp_type == 'multi_thread'):
            client_node.close()
            return data_response
        if(data_response.get('status')):
            returnObj['status'] = data_response['status']
        else:
            returnObj['status'] = None
        #returnObj['ddlfile'] = node['ddlfile']
        returnVal.append(returnObj)
        client_node.close()
    except socket_error as e:
        print ('[' + node['url']+ ']:',e)
"""
function: count_db_nodes()
parameter: (string) cat_db: catalog database's name
return: (int) numnodes
This function will count the number of nodes in catalog db
The number of nodes is based on the nodeid. So, if there are
more than one table with the same nodeid, it will only count as one node
"""
def count_db_nodes(cat_db):
    nList = []
    for node in cat_db:
        if not (node['id'] in nList):
            nList.append(node['id'])
    return len(nList)
