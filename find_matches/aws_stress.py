import psycopg2
import time
import random
connect_str_aws_reader = f"dbname='dummy_users' user='yoni' host='voila-aurora-cluster-instance-1-us-east-1d.ck82h9f9wsbf.us-east-1.rds.amazonaws.com' " + \
                        "password='dordordor'"

conn_aws = psycopg2.connect(connect_str_aws_reader)



def perform_query_aws(offset=0):
    min_age = random.randint(18,30)
    max_age = random.randint(40,60)
    typical_query_no_rand = f'select * from aws_users2 where age >= {min_age} and age <= {max_age} and gender_index = 1 and region_index = 0 offset {offset} limit 10000'
    t1 = time.time()
    with conn_aws.cursor() as cursor:
        cursor.execute(typical_query_no_rand)
        results = cursor.fetchall()
    t2 = time.time()

    print(f'it toook {t2-t1} seconds to perform query, going to sleep now')
    time.sleep(3600)


perform_query_aws()