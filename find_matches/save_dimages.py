from sys import argv
import psycopg2
import pickle
from psycopg2.extras import RealDictCursor
import os
from sql_consts import SQL_CONSTS
from psycopg2.extras import RealDictCursor
from tqdm import tqdm
from postgres_client import PostgresClient
from sys import argv
import os



MALE_FOLDER='/data/dummy_users_images/Roar'
FEMALE_FOLDER='/data/dummy_users_images/Doar'

DATA_MALE_FOLDER='/home/yoni/datasets/pof_data/Roar'
DATA_FEMALE_FOLDER='/home/yoni/datasets/pof_data/Doar'

pg_client = PostgresClient(host='localhost',database='dummy_users')

def get_path_dummy_users_images(path):
    gender = path.split('/')[0]
    if gender not in ['Male','Female']:
        raise ValueError(f'{path} doesnt start with a gender')
    if gender=='Male':
        return os.path.join(MALE_FOLDER,path)
    else:
        return os.path.join(FEMALE_FOLDER,path)
def get_full_path_data(folder):
    gender = folder.split('/')[0]
    if gender not in ['Male','Female']:
        raise ValueError(f'{folder} doesnt start with a gender')
    if gender=='Male':
        return os.path.join(DATA_MALE_FOLDER,folder)
    else:
        return os.path.join(DATA_FEMALE_FOLDER,folder)


def get_dummy_user_images(user):
    # Input : a dict of pof user. Output: list of valid images
    #user_images = get_user_objects_keys(user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value])
    
    actual_folder = os.path.join(get_path_dummy_users_images(user['folder']), str(user['pof_id']))
    user_images = os.listdir(actual_folder)
    user_images.sort()
    user_id = user['pof_id']

    return user_images
DUMMY_BUCKET = 'com.voiladating.dummy'

connect_str_papush = f"dbname='dummy_users' user='yoni' host='192.116.48.67' " + \
                     "password='dor'"
postgres_conn = psycopg2.connect(connect_str_papush)
print(argv)
for age in range(int(argv[1]),int(argv[2])):
    with postgres_conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f'select * from dummy_users where age={age}')
        users_for_some_age = cursor.fetchall()



    for some_user in tqdm(users_for_some_age):

        user_images = get_dummy_user_images(some_user)
        some_user = dict(some_user)
        for priority,user_image in enumerate(user_images):

                image_data = {
                    SQL_CONSTS.ImageColumns.BUCKET_NAME.value : DUMMY_BUCKET,
                    SQL_CONSTS.ImageColumns.FILENAME:user_image,
                    SQL_CONSTS.ImageColumns.IS_PROFILE : priority==0,
                    SQL_CONSTS.ImageColumns.PRIORITY:priority,
                    SQL_CONSTS.ImageColumns.USER_ID:str(some_user['pof_id']),
                    SQL_CONSTS.ImageColumns.TYPE:'in_profile'
                }
                pg_client._update_table_by_dict(table_name='dummy_users_images',data = image_data,primary_key=SQL_CONSTS.ImageColumns.PRIMARY_KEY.value)

        