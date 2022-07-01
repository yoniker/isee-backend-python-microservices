import psycopg2
import time
import pandas as pd
from sqlalchemy import create_engine

# host = os.getenv('RD_HOST_NAME')or 'db.ck82h9f9wsbf.us-east-1.rds.amazonaws.com'

connect_str_papush = f"dbname='pof' user='yoni' host='192.116.48.67' " + \
                     "password='dor'"
postgres_conn = psycopg2.connect(connect_str_papush)

# import mysql.connector
#
# mydb = mysql.connector.connect(
#   host="localhost",
#   user="root",
#   password="dordor",
#   auth_plugin='mysql_native_password'
# )
#
# print(mydb)





aws_users_table = pd.read_sql_query('select * from aws_users', postgres_conn)
# my_sql_engine = create_engine("mysql+pymysql://" + 'root' + ":" + 'dordor' + "@" + 'localhost' + "/" + 'pof')
# aws_users_table.to_sql(name='aws_users',con=my_sql_engine)