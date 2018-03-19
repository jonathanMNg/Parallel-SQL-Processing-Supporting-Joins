from server_functions import *

db_conn = create_connection(':memory:')
c = db_conn.cursor()
c.execute("CREATE TEMP TABLE COURSES(sid INTEGER, course char(80))");
c.execute("INSERT INTO COURSES(sid, course) VALUES (1, 'CS')");
c.execute("INSERT INTO COURSES(sid, course) VALUES (1, 'CS')");
c.execute("INSERT INTO COURSES(sid, course) VALUES (1, 'CS')");
c.execute("INSERT INTO COURSES(sid, course) VALUES (1, 'CS')");
c.execute("INSERT INTO COURSES(sid, course) VALUES (1, 'CS')");
c.execute("SELECT * FROM COURSES");

row = c.fetchall()

print (row);
