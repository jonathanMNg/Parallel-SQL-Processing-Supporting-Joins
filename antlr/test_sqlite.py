from parse_sql import parse_sql_table_name

def main():
    sql = """select first_name, last_name, order_date, order_amount
from customers c
inner join orders o
on c.customer_id = o.customer_id"""
    print(parse_sql_table_name(sql))

if __name__ == '__main__':
    main()
