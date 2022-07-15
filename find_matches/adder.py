from postgres_client import PostgresClient
import time

aurora_reader_host = 'voila-aurora-cluster.cluster-ro-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
aurora_username = 'yoni'
aurora_password = 'dordordor'


connect_str_papush = f"dbname='dummy_users' user='yoni' host='192.116.48.67' " + \
                        "password='dor'"


aurora_client = PostgresClient(database = 'dummy_users',user=aurora_username,password=aurora_password,host=aurora_reader_host)

for age in range(21,120):
    print(f'doing age {age}')
    t1=time.time()
    aurora_client.add_people(min_age=age)
    t2=time.time()
    print(f'it took {t2-t1}')


'''
DELETE FROM
    dummy_users_with_fr a
        USING dummy_users_with_fr b
WHERE
    a.index < b.index
    AND a.pof_id = b.pof_id;


select * from dummy_users_images where user_id in ('149921077','155505712','161836831')

pg_dump dummy_users -t dummy_users_images> dummy_users_images.dump

'''