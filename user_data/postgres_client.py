import psycopg2.pool
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_consts import SQL_CONSTS
from psycopg2.errors import UniqueViolation
from contextlib import contextmanager
import time
import pandas as pd
import pandas.io.sql as sqlio
import pickle




class PostgresClient:
    def __init__(self,minconn=100,maxconn=200,database='real_users',
                                                         user='yoni',
                                                         password='dor',
                                                         host='localhost'):
        self.host = host
        self.user = user
        self.pool = psycopg2.pool.ThreadedConnectionPool(minconn=minconn,maxconn=maxconn,
                                                         database=database,
                                                         user=user,
                                                         password=password,
                                                         host=host,
                                                         cursor_factory=RealDictCursor
                                                         )
        self.autocommit=True

    def __repr__(self) -> str:
        return 'Postgres Client @'+self.user+'@'+self.host
        
    @contextmanager
    def get_connection(self):
        con = self.pool.getconn()
        con.autocommit = self.autocommit
        try:
            yield con
        finally:
            self.pool.putconn(con,close=True)
    def _update_table_by_dict(self, table_name, data, primary_key):
        '''

        Args:
            table_name: name of the table for which we want to insert
            data: dictionary with keys=column names, and values=values to insert at those columns
            primary_key:

        Returns:

        '''
        if type(data) != dict: raise ValueError(f'Error inserting into table,Expecting a dictionary, got {type(data)}')
        keys = data.keys()
        columns = ','.join(keys)
        values = ','.join(['%({})s'.format(k) for k in keys])
        insert = 'insert into {0} ({1}) values ({2})'.format(table_name, columns, values)
        try:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    #print(cursor.mogrify(insert, data))
                    cursor.execute(insert, data)
    
        except UniqueViolation as _:
            with self.get_connection() as connection:
                with connection.cursor() as cursor:
                    update = f'update {table_name} set '
                    update += ','.join([f' {k}=%({k})s ' for k in data.keys()])
                    if primary_key[0] == '(':  # multiple value primary key
                        if primary_key[-1] != ')':
                            raise ValueError('Bad multiple primary key')
                        columns_names = primary_key[1:-1].split(',')
                        primary_key_str = ','.join([f'%({column_name})s' for column_name in columns_names])
                        primary_key_str = '(' + primary_key_str + ')'
                    else:
                        primary_key_str = f'%({primary_key})s'
                    update += f" where {primary_key}={primary_key_str}"
                    #print(cursor.mogrify(update, data))
                    cursor.execute(update, data)

    def create_users_table(self):
        # taste_mix_ratio double precision,radius double precision,primary key (decider_facebook_id) );
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE TABLE users ('
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_UID} varchar NOT NULL,'
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_EMAIL} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_NAME} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_IMAGE_URL} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_SIGNIN_PROVIDER} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FIREBASE_PHONE_NUMBER} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FACEBOOK_ID} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FACEBOOK_BIRTHDAY} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.APPLE_ID} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.NAME} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FCM_TOKEN} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FACEBOOK_PROFILE_IMAGE_URL} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.ADDED_DATE} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.UPDATE_DATE} double precision NOT NULL,'
                                     f'{SQL_CONSTS.UsersColumns.MIN_AGE} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.MAX_AGE} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.TASTE_MIX_RATIO} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.GENDER_PREFERRED} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FILTER_NAME} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.AUDITION_COUNT} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FILTER_DISPLAY_IMAGE} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.RADIUS} double precision,'
        
                                     f'{SQL_CONSTS.UsersColumns.CELEB_ID} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.EMAIL} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.USER_GENDER} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.USER_DESCRIPTION} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.SHOW_USER_GENDER} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.RELATIONSHIP_TYPE} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.USER_BIRTHDAY} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.LONGITUDE} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.LATITUDE} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.LOCATION_DESCRIPTION} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.SEARCH_DISTANCE_ENABLED} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.SHOW_DUMMY_PROFILES} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.USER_BIRTHDAY_TIMESTAMP} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.JOB_TITLE} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.HEIGHT_IN_CM} double precision,'
                                     f'{SQL_CONSTS.UsersColumns.SCHOOL} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.RELIGION} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.ZODIAC} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.FITNESS} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.SMOKING} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.DRINKING} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.EDUCATION} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.CHILDREN} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.COVID_VACCINE} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.HOBBIES} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.PETS} varchar,'
                                     f'{SQL_CONSTS.UsersColumns.TEXT_SEARCH} varchar,'
                               
                               
        
        
        
        
                                     f'primary key ({SQL_CONSTS.UsersColumns.FIREBASE_UID}) '
                                     f');')

    def create_decisions_table(self):
        # taste_mix_ratio double precision,radius double precision,primary key (decider_facebook_id) );
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE TABLE {SQL_CONSTS.TablesNames.DECISIONS} ('
                               f'{SQL_CONSTS.DecisionsColumns.DECIDER_ID} varchar NOT NULL,'
                               f'{SQL_CONSTS.DecisionsColumns.DECIDEE_ID} varchar NOT NULL,'
                               f'{SQL_CONSTS.DecisionsColumns.DECISION} varchar,'
                               f'{SQL_CONSTS.DecisionsColumns.DECISION_TIMESTAMP} double precision NOT NULL,'
                               f'primary key {SQL_CONSTS.DecisionsColumns.PRIMARY_KEY} '
                               f');')
    
    
    def insert_new_image(self,upload_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.IMAGES.value,data=upload_data,primary_key=SQL_CONSTS.ImageColumns.PRIMARY_KEY)
    
    
    def get_user_profile_images(self,user_id):
        '''
        original query:
        select * from images where user_id = 'kRlw3NNKk5aavKfYEupXroBcfYp1' and type = 'in_profile' order by priority asc;
        '''
        sql_cmd = f"select * from {SQL_CONSTS.TablesNames.IMAGES.value} where {SQL_CONSTS.ImageColumns.USER_ID}=%s "\
        f"and {SQL_CONSTS.ImageColumns.TYPE.value}=%s order by {SQL_CONSTS.ImageColumns.PRIORITY} asc"
        data = (user_id,SQL_CONSTS.ImagesConsts.IN_PROFILE_TYPE.value,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results
    
    
    def swap_images_priorities(self,image1_key,image2_key):
        """
        Original command:
        UPDATE images dst SET priority = src.priority
        FROM images src
        WHERE dst.filename IN(filename1,filename2)
        AND src.filename IN(filename1,filename2)
        AND dst.filename <> src.filename
        """
        sql_cmd = f"UPDATE {SQL_CONSTS.TablesNames.IMAGES.value} dst SET {SQL_CONSTS.ImageColumns.PRIORITY.value}=src.{SQL_CONSTS.ImageColumns.PRIORITY.value} "\
        f"FROM {SQL_CONSTS.TablesNames.IMAGES.value} src "\
        f"WHERE dst.{SQL_CONSTS.ImageColumns.FILENAME.value} IN (%s,%s) "\
        f"AND src.{SQL_CONSTS.ImageColumns.FILENAME.value} IN (%s,%s) " \
        f"AND dst.{SQL_CONSTS.ImageColumns.FILENAME.value} <> src.{SQL_CONSTS.ImageColumns.FILENAME.value}"
        data = (image1_key,image2_key,image1_key,image2_key)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd,data)
    
    
    def delete_image(self,image_key):
        """
        SQL command is
        update images set type='removed' where filename=filename1
        :return:
        """
        sql_cmd = f"UPDATE {SQL_CONSTS.TablesNames.IMAGES.value} set "\
        f"{SQL_CONSTS.ImageColumns.TYPE.value}=%s WHERE {SQL_CONSTS.ImageColumns.FILENAME.value}=%s"
        data=(SQL_CONSTS.ImagesConsts.DELETED.value,image_key)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                status_line = cursor.execute(sql_cmd, data)
        return status_line

    def get_celeb_images(self,celeb_name):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.CELEBS_S3_IMAGES.value} where {SQL_CONSTS.CELEBS_S3_ImagesColumns.CELEBNAME.value}=%s order by priority asc'
                data=(celeb_name,)
                cursor.execute(sql_cmd,data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def update_user_data(self, user_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value, data=user_data,primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID)
