
import os
import psycopg2
from flask import Flask,jsonify
import time
import random
app = Flask(__name__)
#host = os.getenv('RD_HOST_NAME')or 'db.ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
connect_str_aws = f"dbname='dummy_users' user='yoni' host='voila-aurora-cluster-instance-1.ck82h9f9wsbf.us-east-1.rds.amazonaws.com' " + \
                        "password='dordordor'"

connect_str_aws_reader = f"dbname='dummy_users' user='yoni' host='voila-aurora-cluster-instance-1-us-east-1d.ck82h9f9wsbf.us-east-1.rds.amazonaws.com' " + \
                        "password='dordordor'"

connect_str_papush = f"dbname='dummy_users' user='yoni' host='192.116.48.67' " + \
                        "password='dor'"
conn_aws = psycopg2.connect(connect_str_aws)
conn_papush = psycopg2.connect(connect_str_papush)
conn_reader_aws = psycopg2.connect(connect_str_aws_reader)
@app.route('/matches/perform_query_aws/<offset>')
def perform_query_aws(offset):
    min_age = random.randint(18,30)
    max_age = random.randint(40,60)
    typical_query_no_rand = f'select * from aws_users2 where age >= {min_age} and age <= {max_age} and gender_index = 1 and region_index = 0 offset {offset} limit 1000'
    t1 = time.time()
    with conn_aws.cursor() as cursor:
        cursor.execute(typical_query_no_rand)
        results = cursor.fetchall()
    t2 = time.time()
    return jsonify({'time_elapsed':t2-t1, 'min_age':min_age,'max_age':max_age})

@app.route('/matches/perform_query_reader/<offset>')
def perform_query_aws_reader(offset):
    min_age = random.randint(18, 30)
    max_age = random.randint(40, 60)
    typical_query_no_rand = f'select * from aws_users2 where age >= {min_age} and age <= {max_age} and gender_index = 1 and region_index = 0 offset {offset} limit 1000'
    t1 = time.time()
    with conn_reader_aws.cursor() as cursor:
        cursor.execute(typical_query_no_rand)
        results = cursor.fetchall()
    t2 = time.time()
    return jsonify({'time_elapsed':t2-t1, 'min_age':min_age,'max_age':max_age})


@app.route('/matches/perform_query_papush/<offset>')
def perform_query_papush(offset):
        typical_query_no_rand = f'select * from aws_users2 where age >= 28 and age <= 45 and gender_index = 1 and region_index = 0 offset {offset} limit 1000'
        t1 = time.time()
        with conn_papush.cursor() as cursor:
            cursor.execute(typical_query_no_rand)
            results = cursor.fetchall()
        t2 = time.time()
        return jsonify({'time_elapsed': t2 - t1})


@app.route('/matches/healthcheck')
def say_healthy():
    return jsonify({'status':'matches service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20002,host="0.0.0.0",debug=False)

#docker run -d -p 20002:20002/tcp find_matches:5



