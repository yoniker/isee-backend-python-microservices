
import os
import psycopg2
from flask import Flask,jsonify
import time
import random
from postgres_client import PostgresClient
app = Flask(__name__)

aurora_reader_host = 'voila-aurora-cluster.cluster-ro-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


connect_str_papush = f"dbname='dummy_users' user='yoni' host='192.116.48.67' " + \
                        "password='dor'"


aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_reader_host)
conn_papush = psycopg2.connect(connect_str_papush)

@app.route('/matches/perform_query_aws/')
def perform_query_aws():
    min_age = random.randint(18,30)
    max_age = random.randint(40,60)
    t1 = time.time()
    result = aurora_client.get_matches()
    t2 = time.time()

    return jsonify({'time_elapsed':t2-t1, 'result':result})


@app.route('/matches/healthcheck')
def say_healthy():
    return jsonify({'status':'matches service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20002,host="0.0.0.0",debug=False)

#docker run -d -p 20002:20002/tcp find_matches:5



