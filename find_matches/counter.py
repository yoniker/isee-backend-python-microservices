import psycopg2
import pickle
from psycopg2.extras import RealDictCursor
connect_str_papush = f"dbname='pof' user='yoni' host='192.116.48.67' " + \
                     "password='dor'"
postgres_conn = psycopg2.connect(connect_str_papush)

stats = {'Female':{},'Male':{}}

for gender in ['Female','Male']:
    for age in range(18,105):
        print(f'at {gender} {age}')
        with postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(f"select count(*) from aws_users2 where gender='{gender}' and age={age}")
            results = cursor.fetchall()
            stats[gender][age] = results[0].get('count',0)
with open('stats.pickle', 'wb') as handle:
    pickle.dump(stats, handle, protocol=pickle.HIGHEST_PROTOCOL)