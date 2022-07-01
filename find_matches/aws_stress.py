import psycopg2
import time
connect_str_aws = f"dbname='pof' user='yoni' host='voila-postgres-db.ck82h9f9wsbf.us-east-1.rds.amazonaws.com' " + \
                  "password='dordordor'"

conn_aws = psycopg2.connect(connect_str_aws)



def perform_query_aws():
    t1 = time.time()
    with conn_aws.cursor() as cursor:
        cursor.execute(
            f"select count(*) from aws_users   where   age>=28  and age<=45  and lower(gender) = 'female' and headline like 'Loo%'  and true;")
    t2 = time.time()
    return t2-t1

while True:
    print(f'it took {perform_query_aws() } to do the query')



'''
3.  Stress-test DB (verify it can do many customers at the same time)

4. Complete the find_matches micro-service

-Learn how to add another instance to the aws ecs cluster

'''