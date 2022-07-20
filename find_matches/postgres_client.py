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
    def __init__(self,minconn=1,maxconn=20,database='real_users',
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
        self.stats = pickle.load(open('dummy_users_stats.pkl', 'rb'))

    def __repr__(self) -> str:
        return 'Postgres Client @'+self.user+'@'+self.host
        
    @contextmanager
    def get_connection(self):
        con = self.pool.getconn()
        con.autocommit = self.autocommit
        try:
            yield con
        finally:
            self.pool.putconn(con)
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

    def _fraction_of_users(self, gender_index, min_age=None, max_age=None,desired_num_users = 500):
        min_age, max_age = round(min_age),round(max_age)
        if gender_index == 0:
            gender = SQL_CONSTS.DummyUsersGender.FEMALE.value
        elif gender_index == 1:
            gender = SQL_CONSTS.DummyUsersGender.MALE.value
        else:
            gender = None
        genders = ['Male','Female'] if gender is None else [gender]
        if min_age is None: min_age = 18
        if max_age is None: max_age = 100
        ages = range(min_age,max_age+1)
        num_expected_users_in_query = 0
        for gender in genders:
            for age in ages:
                num_expected_users_in_query += self.stats.get(gender, {}).get(age, 0)
        if num_expected_users_in_query==0 : return 100
        return desired_num_users* 100.0 / (num_expected_users_in_query)

            
    def get_user_profile(self, user_id):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'select * from {SQL_CONSTS.TablesNames.USERS.value} where {SQL_CONSTS.UsersColumns.FIREBASE_UID.value}=%s',(user_id,))
                results = cursor.fetchall()
                if len(results)==0:
                    return {}
                return dict(results[0])

    def get_dummy_user_images(self,user_id):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'select * from {SQL_CONSTS.TablesNames.DUMMY_USERS_IMAGES.value} where {SQL_CONSTS.DummyUsersImagesColumns.USER_ID.value}=%s',(user_id,))
                results = cursor.fetchall()
                return [dict(result) for result in results]

    def get_dummy_users_images(self,users_ids):
        if len(users_ids)==0:
            return []
        user_ids = tuple(str(user_id) for user_id in users_ids)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'select * from {SQL_CONSTS.TablesNames.DUMMY_USERS_IMAGES.value} where {SQL_CONSTS.DummyUsersImagesColumns.USER_ID.value} in %s',(user_ids,))
                results = cursor.fetchall()
                return [dict(result) for result in results]


    def get_dummy_matches(self,lat=None,lon=None,radium_in_kms=None,min_age=None,max_age=None,gender_index=None,uid=None,need_fr_data=False,text_search = '',max_num_users=1000):
        
        location_based_search = all([x is not None for x in [lat,lon,radium_in_kms]])
        text_based_search = len(text_search) > 0
        if not (location_based_search or text_based_search): #We potentially have to go over all the huge table,let's see if that is the case and if so sample from it instead of going over the entire table.
            percents_in_db = self._fraction_of_users(gender_index=gender_index, min_age=min_age, max_age=max_age,
                                            desired_num_users=max_num_users)
        else:
            percents_in_db = 100
        
        table_sample_text = f' tablesample system({percents_in_db}) ' if percents_in_db<10  else ' '
        
        

        #The idea is to change the query string, and query args in accordance with the parameters required
        query = f'SELECT * FROM {SQL_CONSTS.TablesNames.DUMMY_USERS.value}  {table_sample_text} WHERE true '
        query_args = [] 
        if location_based_search:
            query += f' and earth_box(ll_to_earth(%s,%s ),%s*1000/1.609) @> ll_to_earth({SQL_CONSTS.UsersColumns.LATITUDE.value}, {SQL_CONSTS.UsersColumns.LONGITUDE.value}) '
            query_args += [lat,lon,radium_in_kms]

        if min_age is not None:
            query += ' and age>=%s '
            query_args+= [min_age]
        if max_age is not None:
            query += ' and age<=%s '
            query_args+= [max_age]
        if gender_index is not None:
            query += ' and gender_index=%s'
            query_args += [gender_index]
        if text_search is not None and len(text_search)>0:
            query +=  f" and lower(description) like %s "
            query_args += ['%'+text_search.lower()+'%']
        if uid is not None:
            query += f' and not cast ({SQL_CONSTS.DummyUsersColumns.POF_ID.value} as varchar)  in (select {SQL_CONSTS.DecisionsColumns.DECIDEE_ID.value} from {SQL_CONSTS.TablesNames.DECISIONS.value} where {SQL_CONSTS.DecisionsColumns.DECIDER_ID.value}=%s) '
            query_args += [uid]
        query += f' order by random() limit {max_num_users}'
        if need_fr_data:
            query = f'with selected_users as ({query}) ' \
                             f'select * from (selected_users  join dummy_users_fr_data on selected_users.pof_id=dummy_users_fr_data.pof_id)'
        print(f'got here,query is {query}')
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                full_query = cursor.mogrify(query,query_args)
                print(full_query)
                data = sqlio.read_sql_query(full_query, connection)
                return data

    def user_info(self, uid):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
        
                cursor.execute(f'select * from {SQL_CONSTS.TablesNames.USERS.value} where {SQL_CONSTS.UsersColumns.FIREBASE_UID.value}=%s', (uid,))
                results = cursor.fetchall()
        if len(results) ==0:
            return {}
        return dict(results[0])

    def get_celeb_embeddings(self,celeb_name):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'select * from {SQL_CONSTS.TablesNames.CELEBS_FR_DATA.value} where {SQL_CONSTS.CELEBS_FR_DataColumn.CELEBNAME.value}=%s', (celeb_name,))
                results = cursor.fetchall()
        if len(results) ==0:
            return []
        return dict(results[0])[SQL_CONSTS.CELEBS_FR_DataColumn.FR_DATA.value]