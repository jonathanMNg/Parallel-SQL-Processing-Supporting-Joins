# Parallel-SQL-Processing-Supporting-Joins
ICS421-Assignment 3

## What it does?
- Follow the other projects, [DDL-Processing](https://github.com/jonathanMNg/ddl-processing-parallel), and [Naive-SQL-Processing-for-Parallel-DBMS ](https://github.com/jonathanMNg/Naive-SQL-Processing-for-Parallel-DBMS) this program is combination of all those programs. It can load, query ddlfile such as SQL and CSV in multi-threaded CONCURRENTLY.
- There are two main files in this program:
  - `runSQL.py`: this program is the main program which runs on the client side. It will receive the configuration from the `cluster.cfg` then process the input `ddlfile` **CONCURRENTLY USING THREADS**. Then it will display the result of the rows it retrieved from the SQL.
  - `parDBd.py`: this program is for the server side cluster machines. It will listen and accept configuration data from the client side, then process the data on the server side. Then send ONLY the requested results back to the clients.
## How it works?

### Files included:
- Program files:
  - `runSQL.py`: run on client machines. When executed, this program will connect to the cluster server machines that their configuration is stored in the catalog database. Then output the query it was given in the command line.
  - `parDBd.py`: run on server machines. When executed, this program will create a connection and waits for the input(config data, sql query) from the client side, then it will execute the query based on the configuration. In the end, it will send back data about the query whether it success or fails to execute.
- Function files:
  - `client_functions.py`: contains functions that are used *mostly* on client machines.
  - `server_functions.py`: contains functions that are used *mostly* on server machines.
- OOP files:
  - `cluster.py`: the base class for the cluster machines object.
  - `cluster_client.py`: the class for the client socket that run on client machine.
  - `cluster_server.py`: the class for the server socket that run on server machines.
- DDL files:  
  - `create_table_courses.sql`: contains the query that will create the table on the server machine's database.
  - `create_table_students.sql`: contains the query that will create the table on the server machine's database.
  - `select_join.sql`: contains the query that will select data from the table on the server machine's database.
  - `courses.csv`: contains the data in csv-form that will be loaded to cluster machine database.
  - `students.csv`: contains the data in csv-form that will be loaded to cluster machine database.
- Configuration files:
  - `init_cluster.cfg`: contains configuration to init the databases
  - `cluster.cfg`: contains configuration for loading the table into partitions
- ANTLR files: (use to parse the SQL statement)
  - `antlr4`: the directory for the ANTLR language parser
  - `parse_sql.py`: the file that store the function that I used to parse the name of the table from the SQL statement.
### Tested Enviroment:
- Ubuntu (docker)
- macOSX
### Requirements:
- [python3](https://www.python.org/download/releases/3.0/)
- [sqlite3](https://www.sqlite.org)
- `iputils-ping`, `iproute`, `dnsutils`
```
apt-get -y install iputils-ping
apt-get -y install iproute
apt-get -y install dnsutils
```

### Installation:
- Clone or download this repository.

### Configure `cluster.cfg`
- In order for this program to work. You need to configure the `init_cluster.cfg` and `cluster.cfg` to give the right configuration for the server cluster computers.

#### **`init_cluster.cfg`**
**Need to configure:**
- `numnodes:` the number of nodes in database
- `catalog.hostname:` hostname for catalog database ip.address/db_name
- `node1.hostname:` hostname for node1 database ip.address/db_name
- `node2.hostname:` hostname for node2 database ip.address/db_name
```
numnodes=2 //number of nodes in cluster machines

catalog.driver=com.ibm.db2.jcc.DB2Driver
catalog.hostname=192.168.1.8:50001/mycatdb

node1.driver=com.ibm.db2.jcc.DB2Driver
node1.hostname=192.168.1.8:50002/mydb1

node2.driver=com.ibm.db2.jcc.DB2Driver
node2.hostname=192.168.1.8:50003/mydb2
```

#### **`cluster.cfg`**
**Need to configure:**
- `numnodes:` the number of nodes in database (not required for **hash** partition)
- `catalog.hostname:` hostname for catalog database ip.address/db_name
- `localnode.hostname:` hostname for the localnode on cluster machine that will execute the SQL, and send back the result to the client.
- `tablename:` name of the table need to run on cluster machines
- `delimiter:` divider for the csv file (e.g: `,` `|` `-` )
  - **Warning** if you don't configure the delimiter right, the `loadCSV.py` would not run because the CSV can't be load properly
- `partition.method:` name of method for the partition
- `partition.column:` the column that will use for the partition
- `partition.node{#}.param1 and partition.node{#}.param2`: range for the partition (required for **range** partition only)
- `partition.param1`: number of nodes for the partition (required for **hash** partition only)


**With No Partition**
```
catalog.driver=com.ibm.db2.jcc.DB2Driver
catalog.hostname=192.168.1.8:50001/mycatdb
delimiter=|
tablename=BOOKS
partition.method=notpartition
partition.column=price

numnodes=2
```

**With Range Partition**
```
catalog.driver=com.ibm.db2.jcc.DB2Driver
catalog.hostname=192.168.1.8:50001/mycatdb
delimiter=|
tablename=BOOKS
partition.method=range
partition.column=price

numnodes=2
partition.node1.param1=0
partition.node1.param2=10

partition.node2.param1=10
partition.node2.param2=20
```

**With Hash Partition**
```
catalog.driver=com.ibm.db2.jcc.DB2Driver
catalog.hostname=192.168.1.8:50001/mycatdb
delimiter=|
tablename=BOOKS
partition.method=hash
partition.column=price

partition.param1=2
```
### Configure `ddlfile`
- In order to run, the programs need to have at least one table on each server machine. And a `dTable` in the catalog that contains information of each node on the cluster machine.
- The `create_table_students.sql` contains the query to create the table `STUDENTS`
- The `create_table_students.sql` contains the query to create the table `COURSES`
- The `select_join.sql` file contains the query statements that query the `STUDENTS` and the `COURSES` tables.
- The `students.csv` file contains the csv-form data to load into the cluster machine.
- The `courses.csv` file contains the csv-form data to load into the cluster machine.

### Run
- **Warning** Before run the program, make sure you have filled in all the appropriate configuration in `init_cluster.cfg` and `cluster.cfg` file.
#### Init database
- Fire up the server machines:

```
python3 ./parDBd.py 192.168.1.8 50001 &
python3 ./parDBd.py 192.168.1.8 50002 &
python3 ./parDBd.py 192.168.1.8 50003
```

- You should notice that there are two arguments that I used for the server machines are `192.168.1.8` as host, and `50001, 50002, 50003` as port. So there are 3 servers that are listening.

- On the client machine, type:

```
python3 ./runSQL.py ./init_cluster.cfg ./create_table_students.sql
python3 ./runSQL.py ./init_cluster.cfg ./create_table_courses.sql
```
**Expected outcomes:**

```
[192.168.1.8:50002/mydb1]: create_table_students.sql success.
[192.168.1.8:50003/mydb2]: create_table_courses.sql success.
[192.168.1.8:50001/mycatdb]:  catalog updated.
```
If your output is different, you should:
- Take a look at your `cluster.cfg` and `init_cluster.cfg` file.
- Check if any database file existed, if so, delete all the database file
- Go back to **Init database** step
#### Load data to database
- Fire up the server machines (same as above)
- On the client machine, type:
```
python3 ./runSQL.py ./cluster.cfg ./students.csv
python3 ./runSQL.py ./cluster.cfg ./courses.csv
```
**Output:**

- **Not Partition**
```
[192.168.1.8:50002/mydb1]: students.csv 5 rows inserted.
[192.168.1.8:50003/mydb2]: courses.csv 5 rows inserted.
[192.168.1.8:50001/mycatdb]:  catalog updated.
```
#### Retrieve data from database
Since we already loaded data into our database tables. Let take a look:

`mydb1:`
```
sqlite> .tables
STUDENTS
sqlite> PRAGMA table_info ('STUDENTS');
0|sid|INTEGER|0||0
1|sname|char(80)|0||0
sqlite> select * FROM STUDENTS;
1|Jane Doe
2|Darius
3|Draven
4|Xavier
5|Steve
sqlite>
```
`mydb2:`
```
sqlite> .tables
COURSES
sqlite> PRAGMA table_info ('COURSES');
0|sid|INTEGER|0||0
1|course|char(80)|0||0
sqlite> SELECT * FROM COURSES;
1|CS
2|Math
3|Math
4|Sport
5|CS
sqlite>
```
So when they are joined the table should look like:
```
sid| S.sname  |C.course
-----------------------
1  | Jane Doe | CS
2  | Darius   | Math
3  | Draven   | Math
4  | Xavier   | Sport
5  | Steve    | CS
```
- Fire up the server machines (same as above). **Attention** you don't need to fire up the catalog server since there is no update to the catalog database.

- On the client machine, type:
```
python3 ./runSQL.py ./cluster.cfg ./select_join.sql
```
The select_join.sql will query the name of the students who take the `CS` course. Therefore, the expected result should be the name of thoses students
**Output:**
```
Jane Doe
Steve
[192.168.1.8:50002/mydb1]: ./select_join.sql success.
[192.168.1.8:50003/mydb2]: ./select_join.sql success.

```
According to the illustrated join table above, the output is exactly what the output should be.
