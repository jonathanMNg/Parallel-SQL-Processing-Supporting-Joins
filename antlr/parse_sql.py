from antlr4 import *
from SQLiteLexer import SQLiteLexer
from SQLiteParser import SQLiteParser
from SQLiteListener import SQLiteListener

def parse_sql_table_name(sql_stmt):

    input = InputStream(sql_stmt)
    lexer = SQLiteLexer(input)
    stream = CommonTokenStream(lexer)
    parser = SQLiteParser(stream)
    tree = parser.parse()
    listener = SQLiteListener()
    walker = ParseTreeWalker()
    walker.walk(listener, tree)
    return listener.table_name
