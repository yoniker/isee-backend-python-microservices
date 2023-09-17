import psycopg2.pool
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_consts import SQL_CONSTS
from psycopg2.errors import UniqueViolation
from contextlib import contextmanager
import time


class PostgresClient:
    def __init__(self, minconn=20, maxconn=200, database='real_users',
                 user='yoni',
                 password='dor',
                 host='localhost'):
        self.host = host
        self.user = user
        self.pool = psycopg2.pool.ThreadedConnectionPool(minconn=minconn, maxconn=maxconn,
                                                         database=database,
                                                         user=user,
                                                         password=password,
                                                         host=host,
                                                         cursor_factory=RealDictCursor,
                                                         )
        self.autocommit = True

    def __repr__(self) -> str:
        return 'Postgres Client @' + self.user + '@' + self.host

    @contextmanager
    def get_connection(self, autocommit=None):
        con = self.pool.getconn()
        con.autocommit = self.autocommit if autocommit is None else autocommit
        try:
            yield con
        finally:
            self.pool.putconn(con, close=True)

    def _update_table_by_dict(self, table_name, data, primary_key=None):
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
                    cursor.execute(insert, data)

        except (psycopg2.errors.NotNullViolation, UniqueViolation) as _:
            if primary_key == None:
                raise ValueError('No primary key was provided and value already exists in db')
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
                               f'{SQL_CONSTS.UsersColumns.HAS_FR_DATA.value} varchar,'
                               f'{SQL_CONSTS.UsersColumns.IS_TEST_USER.value} varchar,'
                               f'{SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value} varchar,'
                               f'primary key ({SQL_CONSTS.UsersColumns.FIREBASE_UID}) '
                               f');')

    def create_gallery_table(self):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE TABLE {SQL_CONSTS.TablesNames.GALLERY_IMAGES.value} ('
                               f'{SQL_CONSTS.GalleryColumns.USER_ID} varchar NOT NULL,'
                               f'{SQL_CONSTS.GalleryColumns.TYPE} varchar,'
                               f'{SQL_CONSTS.GalleryColumns.CREATION_TITLE} varchar,'
                               f'{SQL_CONSTS.GalleryColumns.CREATION_ARTIST} varchar,'
                               f'{SQL_CONSTS.GalleryColumns.FILENAME} varchar,'
                               f'{SQL_CONSTS.GalleryColumns.BUCKET_NAME} varchar,'
                               f'{SQL_CONSTS.GalleryColumns.CREATION_TIMESTAMP} double precision,'
                               f'{SQL_CONSTS.GalleryColumns.PRIORITY} bigint,'
                               f'{SQL_CONSTS.GalleryColumns.CREATION_PROMPT} varchar,'
                               
                               f'primary key {SQL_CONSTS.GalleryColumns.PRIMARY_KEY.value} '
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

    def insert_new_image(self, upload_data):
        '''
        Have to have a special insert command as the priority has to be max of current priority+1.
        Raw query:
        insert into images(user_id,bucket_name,filename,type,priority) values ('d1','d1','d1','d1',(select coalesce(max(priority), 0)+1 from images where user_id='5EX44AtZ5cXxW1O12G3tByRcC012'))
        :param upload_data:
        :return:
        '''
        sql_cmd = f'INSERT INTO {SQL_CONSTS.TablesNames.IMAGES.value} (' \
                  f'{SQL_CONSTS.ImageColumns.USER_ID.value},' \
                  f'{SQL_CONSTS.ImageColumns.BUCKET_NAME.value},' \
                  f'{SQL_CONSTS.ImageColumns.FILENAME.value},' \
                  f'{SQL_CONSTS.ImageColumns.TYPE.value},' \
                  f'{SQL_CONSTS.ImageColumns.PRIORITY.value}' \
                  f') VALUES (%s,%s,%s,%s,' \
                  f'(select coalesce(max(priority), 0)+1 from images where user_id=%s)' \
                  f');'
        data = (upload_data[SQL_CONSTS.ImageColumns.USER_ID.value],
                upload_data[SQL_CONSTS.ImageColumns.BUCKET_NAME.value],
                upload_data[SQL_CONSTS.ImageColumns.FILENAME.value],
                upload_data[SQL_CONSTS.ImageColumns.TYPE.value],
                upload_data[SQL_CONSTS.ImageColumns.USER_ID.value]
                )
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)

    def insert_new_gallery_image(self, upload_data):
        '''
        Have to have a special insert command as the priority has to be max of current priority+1.
        Raw query:
        insert into images(user_id,bucket_name,filename,type,priority) values ('d1','d1','d1','d1',(select coalesce(max(priority), 0)+1 from images where user_id='5EX44AtZ5cXxW1O12G3tByRcC012'))
        :param upload_data:
        :return:
        '''
        sql_cmd = f'INSERT INTO {SQL_CONSTS.TablesNames.GALLERY_IMAGES.value} (' \
                  f'{SQL_CONSTS.GalleryColumns.USER_ID.value},' \
                  f'{SQL_CONSTS.GalleryColumns.BUCKET_NAME.value},' \
                  f'{SQL_CONSTS.GalleryColumns.FILENAME.value},' \
                  f'{SQL_CONSTS.GalleryColumns.CREATION_PROMPT.value},' \
                  f'{SQL_CONSTS.GalleryColumns.CREATION_ARTIST.value},' \
                  f'{SQL_CONSTS.GalleryColumns.CREATION_TITLE.value},' \
                  f'{SQL_CONSTS.GalleryColumns.CREATION_TIMESTAMP.value},' \
                  f'{SQL_CONSTS.GalleryColumns.TYPE.value},' \
                  f'{SQL_CONSTS.GalleryColumns.PRIORITY.value}' \
                  f') VALUES (%s,%s,%s,%s,%s,%s,%s,%s,' \
                  f'(select coalesce(max(priority), 0)+1 from {SQL_CONSTS.TablesNames.GALLERY_IMAGES.value} where {SQL_CONSTS.GalleryColumns.USER_ID.value}=%s)' \
                  f');'
        data = (upload_data[SQL_CONSTS.GalleryColumns.USER_ID.value],
                upload_data[SQL_CONSTS.GalleryColumns.BUCKET_NAME.value],
                upload_data[SQL_CONSTS.GalleryColumns.FILENAME.value],
                upload_data[SQL_CONSTS.GalleryColumns.CREATION_PROMPT.value],
                upload_data[SQL_CONSTS.GalleryColumns.CREATION_ARTIST.value],
                upload_data[SQL_CONSTS.GalleryColumns.CREATION_TITLE.value],
                upload_data[SQL_CONSTS.GalleryColumns.CREATION_TIMESTAMP.value],
                upload_data[SQL_CONSTS.GalleryColumns.TYPE.value],
                upload_data[SQL_CONSTS.GalleryColumns.USER_ID.value]
                )
        print(f'going to insert into gallery images the values {data}')
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                print(cursor.mogrify(sql_cmd, data))
                cursor.execute(sql_cmd, data)

    def delete_gallery_image(self, image_key, user_id):
        """
        SQL command is
        update images set type='removed' where filename=filename1
        :return:
        """
        sql_cmd = f"DELETE FROM {SQL_CONSTS.TablesNames.GALLERY_IMAGES.value}  WHERE {SQL_CONSTS.ImageColumns.FILENAME.value}=%s and {SQL_CONSTS.GalleryColumns.USER_ID}=%s"
        data = (image_key, user_id,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                status_line = cursor.execute(sql_cmd, data)
        return status_line

    def get_user_gallery_images(self, user_id):
        '''
        original query:
        select * from images where user_id = 'kRlw3NNKk5aavKfYEupXroBcfYp1' and type = 'in_profile' order by priority asc;
        '''
        sql_cmd = f"select * from {SQL_CONSTS.TablesNames.GALLERY_IMAGES.value} where {SQL_CONSTS.GalleryColumns.USER_ID}=%s " \
                  f" order by {SQL_CONSTS.GalleryColumns.PRIORITY} asc"
        data = (user_id,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def get_user_profile_images(self, user_id):
        '''
        original query:
        select * from images where user_id = 'kRlw3NNKk5aavKfYEupXroBcfYp1' and type = 'in_profile' order by priority asc;
        '''
        sql_cmd = f"select * from {SQL_CONSTS.TablesNames.IMAGES.value} where {SQL_CONSTS.ImageColumns.USER_ID}=%s " \
                  f"and {SQL_CONSTS.ImageColumns.TYPE.value}=%s order by {SQL_CONSTS.ImageColumns.PRIORITY} asc"
        data = (user_id, SQL_CONSTS.ImagesConsts.IN_PROFILE_TYPE.value,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def swap_images_priorities(self, image1_key, image2_key):
        """
        Original command:
        UPDATE images dst SET priority = src.priority
        FROM images src
        WHERE dst.filename IN(filename1,filename2)
        AND src.filename IN(filename1,filename2)
        AND dst.filename <> src.filename
        """
        sql_cmd = f"UPDATE {SQL_CONSTS.TablesNames.IMAGES.value} dst SET {SQL_CONSTS.ImageColumns.PRIORITY.value}=src.{SQL_CONSTS.ImageColumns.PRIORITY.value} " \
                  f"FROM {SQL_CONSTS.TablesNames.IMAGES.value} src " \
                  f"WHERE dst.{SQL_CONSTS.ImageColumns.FILENAME.value} IN (%s,%s) " \
                  f"AND src.{SQL_CONSTS.ImageColumns.FILENAME.value} IN (%s,%s) " \
                  f"AND dst.{SQL_CONSTS.ImageColumns.FILENAME.value} <> src.{SQL_CONSTS.ImageColumns.FILENAME.value}"
        data = (image1_key, image2_key, image1_key, image2_key)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)

    def delete_profile_image(self, image_key):
        """
        SQL command is
        update images set type='removed' where filename=filename1
        :return:
        """
        sql_cmd = f"UPDATE {SQL_CONSTS.TablesNames.IMAGES.value} set " \
                  f"{SQL_CONSTS.ImageColumns.TYPE.value}=%s WHERE {SQL_CONSTS.ImageColumns.FILENAME.value}=%s"
        data = (SQL_CONSTS.ImagesConsts.DELETED.value, image_key)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                status_line = cursor.execute(sql_cmd, data)
        return status_line

    def get_celeb_images(self, celeb_name):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.CELEBS_S3_IMAGES.value} where {SQL_CONSTS.CELEBS_S3_ImagesColumns.CELEBNAME.value}=%s order by priority asc'
                data = (celeb_name,)
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def get_free_celeb_images(self, celeb_name):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.FREE_CELEBS_S3_IMAGES.value} where {SQL_CONSTS.CELEBS_S3_ImagesColumns.CELEBNAME.value}=%s order by priority asc'
                data = (celeb_name,)
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def update_user_data(self, user_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value, data=user_data,
                                          primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID)

    @staticmethod
    def canonize_match_data(match_dict):
        # Order user1,user2 in alphabetic order
        if (SQL_CONSTS.MatchColumns.ID_USER1.value not in match_dict) or (
                SQL_CONSTS.MatchColumns.ID_USER2.value not in match_dict):
            raise ValueError('illegal match data')
        if match_dict[SQL_CONSTS.MatchColumns.ID_USER1.value] > match_dict[SQL_CONSTS.MatchColumns.ID_USER2.value]:
            match_dict[SQL_CONSTS.MatchColumns.ID_USER1.value], match_dict[SQL_CONSTS.MatchColumns.ID_USER2.value] = \
                match_dict[SQL_CONSTS.MatchColumns.ID_USER2.value], match_dict[SQL_CONSTS.MatchColumns.ID_USER1.value]

    def update_match(self, match_data):
        PostgresClient.canonize_match_data(match_data)
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.MATCHES,
                                   data=match_data,
                                   primary_key=SQL_CONSTS.MatchColumns.PRIMARY_KEY.value, )

    def get_user_by_id(self, user_id):
        '''
        Get the user's details (name,FCM token etc.) according to the user's id
        :param user_id:
        :return:
        '''
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.USERS.value} where {SQL_CONSTS.UsersColumns.FIREBASE_UID.value} = %s'
                data = (user_id,)
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                if len(results) == 0:
                    return None
                return results[0]

    def clear_user_choices(self, user_id):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'delete from {SQL_CONSTS.TablesNames.DECISIONS.value} where {SQL_CONSTS.DecisionsColumns.DECIDER_ID.value}=%s ',
                    (user_id,)
                )

    def update_decisions(self, decisions_data):
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.DECISIONS.value,
                                   data=decisions_data,
                                   primary_key=SQL_CONSTS.DecisionsColumns.PRIMARY_KEY.value)

    def add_test_user(self, user_id):
        data = {
            SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
            SQL_CONSTS.UsersColumns.IS_TEST_USER.value: SQL_CONSTS.TestUserStates.IS_TEST_USER.value
        }
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value,
                                   data=data,
                                   primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def remove_test_user(self, user_id):
        data = {
            SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
            SQL_CONSTS.UsersColumns.IS_TEST_USER.value: SQL_CONSTS.TestUserStates.IS_NOT_TEST_USER.value
        }
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value,
                                   data=data,
                                   primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def approve_user(self, user_id):
        data = {
            SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
            SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value: SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_APPROVED.value
        }
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value,
                                   data=data,
                                   primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def disapprove_user(self, user_id):
        data = {
            SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
            SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value: SQL_CONSTS.REGISTRATION_STATUS_TYPES.REGISTERED_NOT_APPROVED.value
        }
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value,
                                   data=data,
                                   primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def get_decision(self, decider, decidee):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f'select * from {SQL_CONSTS.TablesNames.DECISIONS.value} where {SQL_CONSTS.DecisionsColumns.DECIDER_ID.value}=%s '
                    f'and {SQL_CONSTS.DecisionsColumns.DECIDEE_ID.value} = %s',
                    (decider, decidee))
                results = cursor.fetchall()
                if len(results) == 0:
                    return {}
                return dict(results[0])

    def post_decision(self, decision_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.DECISIONS.value, data=decision_data,
                                          primary_key=SQL_CONSTS.DecisionsColumns.PRIMARY_KEY.value)

    @staticmethod
    def get_conversation_id(userid1, userid2):
        if userid1 > userid2:
            userid1, userid2 = userid2, userid1  # Swap,this makes sure that the id will be unique between two users
        return f'conversation_{userid1}_with_{userid2}'

    @staticmethod
    def create_insert_command_from_dict(tablename, value_dicts, ignore_conflict=False):
        '''
        Create an insert command which is not SQL injectable (as long as the tablename isnt user input!)
        :param tablename:
        :param value_dicts: dict of keys-column names,values - the values to be inserted
        :return:
        '''
        insert_command = f"insert into {tablename} ({','.join(str(k) for k in value_dicts)}) values ({','.join([' %s ' for _ in range(len(value_dicts))])})"
        if ignore_conflict:
            insert_command += ' ON CONFLICT DO NOTHING'
        values = tuple(value_dicts[k] for k in value_dicts)
        return insert_command, values

    def create_conversation(self, userid, other_user_id):
        conversation_key = PostgresClient.get_conversation_id(userid, other_user_id)
        with self.get_connection(autocommit=False) as connection:
            with connection.cursor() as cursor:
                sql_query = f"select * from {SQL_CONSTS.TablesNames.CONVERSATIONS.value} where {SQL_CONSTS.ConversationsColumns.CONVERSATION_ID.value} = %s"
                data = (conversation_key,)
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
            if len(results) == 0:
                current_time = time.time()
                val_dict = {SQL_CONSTS.ConversationsColumns.CONVERSATION_ID.value: conversation_key,
                            SQL_CONSTS.ConversationsColumns.CREATION_TIME.value: current_time,
                            SQL_CONSTS.ConversationsColumns.CHANGE_TIME.value: current_time}
                with connection.cursor() as cursor:
                    sql_cmd, sql_data = PostgresClient.create_insert_command_from_dict(
                        tablename=SQL_CONSTS.TablesNames.CONVERSATIONS, value_dicts=val_dict)
                    cursor.execute(sql_cmd, sql_data)
                    cursor.execute(
                        f"insert into {SQL_CONSTS.TablesNames.PARTICIPANTS.value}({SQL_CONSTS.ParticipantsColumns.CONVERSATION_ID.value},{SQL_CONSTS.ParticipantsColumns.FIREBASE_UID.value}) values (%s,%s);",
                        (conversation_key, userid))
                    cursor.execute(
                        f"insert into {SQL_CONSTS.TablesNames.PARTICIPANTS.value}({SQL_CONSTS.ParticipantsColumns.CONVERSATION_ID.value},{SQL_CONSTS.ParticipantsColumns.FIREBASE_UID.value}) values (%s,%s);",
                        (conversation_key, other_user_id))
                    connection.commit()

            return conversation_key

    def get_users_by_conversation(self, conversation_id):
        '''
        Get all of the users in a specific conversation
        :param conversation_id:
        :return:
        '''
        with self.get_connection(autocommit=False) as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.USERS.value} where {SQL_CONSTS.UsersColumns.FIREBASE_UID.value} ' \
                          f'in (select {SQL_CONSTS.ParticipantsColumns.FIREBASE_UID.value} from {SQL_CONSTS.TablesNames.PARTICIPANTS.value} where {SQL_CONSTS.ParticipantsColumns.CONVERSATION_ID.value}=%s)'
                data = (conversation_id,)
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def create_receipt_command(self, user_id, message_id, initial_timestamp=0):
        # primary_key = (SQL_CONSTS.ReceiptColumns.USER_ID,SQL_CONSTS.ReceiptColumns.MESSAGE_ID)
        data = {
            SQL_CONSTS.ReceiptColumns.READ_TS.value: initial_timestamp,
            SQL_CONSTS.ReceiptColumns.SENT_TS.value: initial_timestamp,
            SQL_CONSTS.ReceiptColumns.USER_ID.value: user_id,
            SQL_CONSTS.ReceiptColumns.MESSAGE_ID.value: message_id
        }
        sql_cmd, sql_data = self.create_insert_command_from_dict(tablename=SQL_CONSTS.TablesNames.RECEIPTS,
                                                                 value_dicts=data, ignore_conflict=True)
        return sql_cmd, sql_data

    def post_message(self, conversation_id, creator_id, content, created_date, sender_epoch_time, status=None):
        message_id = creator_id + '_' + conversation_id + '_' + str(sender_epoch_time)
        # TODO if not found (name='') throw an error user not found.
        value_dicts = {
            SQL_CONSTS.MessagesColumns.MESSAGE_ID.value: message_id,
            SQL_CONSTS.MessagesColumns.CONTENT.value: content,
            SQL_CONSTS.MessagesColumns.CONVERSATION_ID.value: conversation_id,
            SQL_CONSTS.MessagesColumns.CREATOR_USER_ID.value: creator_id,
            SQL_CONSTS.MessagesColumns.CREATION_DATE.value: created_date,
            SQL_CONSTS.MessagesColumns.CHANGE_DATE.value: created_date,
            SQL_CONSTS.MessagesColumns.MESSAGE_STATUS.value: status,
        }
        post_message_cmd, post_message_data = PostgresClient.create_insert_command_from_dict(
            tablename=SQL_CONSTS.TablesNames.MESSAGES, value_dicts=value_dicts, ignore_conflict=True)

        users = self.get_users_by_conversation(conversation_id=conversation_id)
        with self.get_connection(autocommit=False) as connection:
            with connection.cursor() as cursor:
                cursor.execute(post_message_cmd, post_message_data)
                for user in users:
                    iterated_user_id = user[SQL_CONSTS.UsersColumns.FIREBASE_UID.value]
                    receipt_cmd, receipt_data = self.create_receipt_command(user_id=iterated_user_id,
                                                                            message_id=message_id,
                                                                            initial_timestamp=0 if iterated_user_id != creator_id else created_date)  # TODO: create receipts for all users in conversation
                    cursor.execute(receipt_cmd, receipt_data)
            connection.commit()

            return {'message_details': value_dicts, 'users_in_conversation': users}

    def get_all_user_messages_by_timeline(self, userid, timestamp):
        sql_cmd = f"select * from {SQL_CONSTS.TablesNames.MESSAGES.value} where {SQL_CONSTS.MessagesColumns.CHANGE_DATE.value} > %s and {SQL_CONSTS.MessagesColumns.CONVERSATION_ID.value} in (select {SQL_CONSTS.ParticipantsColumns.CONVERSATION_ID.value} from {SQL_CONSTS.TablesNames.PARTICIPANTS} where {SQL_CONSTS.ParticipantsColumns.FIREBASE_UID.value}=%s);"
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                print(f'DDDDOOOOOORRRRR AT GET USER MESSAGES, I AM GOING TO RUN THE COMMAND:')
                print(f'{cursor.mogrify(sql_cmd, (float(timestamp), userid))}')
                cursor.execute(sql_cmd, (float(timestamp), userid))
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def get_all_user_receipts_by_timeline(self, userid, timestamp):
        '''
        This is the raw version of a query such as the one implements:
        select m.user_id as messages_user_id,*
        from
        (select *
         from messages where conversation_id in (select conversation_id from participants)) m
        inner
        join(select *
        from receipts where
        read_ts > -1 or sent_ts > -1) r
        on
        m.message_id = r.message_id
        '''

        sql_cmd = f"select m.{SQL_CONSTS.MessagesColumns.CREATOR_USER_ID.value} as {SQL_CONSTS.TablesNames.MESSAGES.value}_{SQL_CONSTS.MessagesColumns.CREATOR_USER_ID.value},* from (select * from {SQL_CONSTS.TablesNames.MESSAGES.value} where {SQL_CONSTS.MessagesColumns.CONVERSATION_ID.value} in (select {SQL_CONSTS.ParticipantsColumns.CONVERSATION_ID.value} " \
                  f"from {SQL_CONSTS.TablesNames.PARTICIPANTS.value} where {SQL_CONSTS.ParticipantsColumns.FIREBASE_UID.value}=%s)) m inner join (select * from {SQL_CONSTS.TablesNames.RECEIPTS.value} where {SQL_CONSTS.ReceiptColumns.READ_TS.value}>=%s or {SQL_CONSTS.ReceiptColumns.SENT_TS.value}>=%s) r on m.{SQL_CONSTS.MessagesColumns.MESSAGE_ID.value}=r.{SQL_CONSTS.ReceiptColumns.MESSAGE_ID.value}"
        data = (userid, timestamp, timestamp,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def get_matches_by_timeline(self, userid, timestamp):
        '''

        Get all of the users with any change in status since <timestamp>

        Original query:


        select * from users inner join ((select id_user1 as other_user_id,status from matches where id_user2='10218506033662362' and timestamp_changed>4) union (select id_user2 as other_user_id,status from matches where id_user1='10218506033662362' and timestamp_changed>4)) as relevant_matches on users.facebook_id=relevant_matches.other_user_id


        :param userid:
        :param timestamp:
        :return: All the
        '''

        sql_cmd = f'select * from {SQL_CONSTS.TablesNames.USERS.value} inner join ((select {SQL_CONSTS.MatchColumns.ID_USER1.value} as other_user_id,{SQL_CONSTS.MatchColumns.TIMESTAMP_CHANGED.value} as match_changed_time,{SQL_CONSTS.MatchColumns.STATUS.value} from {SQL_CONSTS.TablesNames.MATCHES.value} where {SQL_CONSTS.MatchColumns.ID_USER2.value}=%s and {SQL_CONSTS.MatchColumns.TIMESTAMP_CHANGED.value}>=%s) ' \
                  f' union (select {SQL_CONSTS.MatchColumns.ID_USER2.value} as other_user_id,{SQL_CONSTS.MatchColumns.TIMESTAMP_CHANGED.value} as match_changed_time,{SQL_CONSTS.MatchColumns.STATUS.value} from {SQL_CONSTS.TablesNames.MATCHES.value} where {SQL_CONSTS.MatchColumns.ID_USER1.value}=%s and {SQL_CONSTS.MatchColumns.TIMESTAMP_CHANGED}>=%s)) as relevant_matches on {SQL_CONSTS.TablesNames.USERS.value}.{SQL_CONSTS.UsersColumns.FIREBASE_UID.value}=relevant_matches.other_user_id order by match_changed_time asc'
        data = (userid, timestamp, userid, timestamp)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def mark_conersation_read(self, userid, conversation_id, timestamp):
        '''
        Update the receipts for userid such that in the conversation there are no unread (=0) receipts.

        The underlying SQL command is
        update receipts set read_ts=8,sent_ts=8 where (message_id_,user_id) in (select message_id_,user_id from receipts where message_id_ in (select message_id_ from messages where conversation_id='conversation_103812845442994_with_107591908393522' and user_id<>'103812845442994') and (read_ts=0 or sent_ts=0))

        Notice that "for now" (possibly indefinetly since I don't think it will matter) sent and read receipts are the same (since there's no received message from client at background message handler)


        :param userid:
        :param conversation_id:
        :return:
        '''

        update_receipt_cmd = f"update {SQL_CONSTS.TablesNames.RECEIPTS.value} set {SQL_CONSTS.ReceiptColumns.READ_TS.value}=%s,{SQL_CONSTS.ReceiptColumns.SENT_TS.value}=%s where " \
                             f"({SQL_CONSTS.ReceiptColumns.MESSAGE_ID.value},{SQL_CONSTS.ReceiptColumns.USER_ID.value}) in (select {SQL_CONSTS.ReceiptColumns.MESSAGE_ID.value},{SQL_CONSTS.ReceiptColumns.USER_ID.value} from {SQL_CONSTS.TablesNames.RECEIPTS.value} where {SQL_CONSTS.ReceiptColumns.MESSAGE_ID.value} in " \
                             f"(select {SQL_CONSTS.MessagesColumns.MESSAGE_ID.value} from {SQL_CONSTS.TablesNames.MESSAGES.value} where {SQL_CONSTS.MessagesColumns.CONVERSATION_ID.value}=%s and {SQL_CONSTS.MessagesColumns.CREATOR_USER_ID.value}<>%s) and ({SQL_CONSTS.ReceiptColumns.READ_TS}=0 or {SQL_CONSTS.ReceiptColumns.SENT_TS}=0))"
        data = (timestamp, timestamp, conversation_id, userid)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(update_receipt_cmd, data)
                try:
                    number_lines_updates = int(cursor.rowcount)
                    return number_lines_updates
                except:
                    pass
                return 0

    def num_users_by_location(self, lat, lon, gender=None, distance_in_km=60):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                statement = f'select count(*) from users where '
                data = []
                if gender is not None:
                    statement += ' gender = %s and '
                    data.append(gender)
                statement += f'earth_distance(ll_to_earth(latitude, longitude), ll_to_earth(%s, %s)) < %s*1000'
                data += [lat, lon, distance_in_km]
                cursor.execute(statement
                               , tuple(data))

                result = cursor.fetchall()
                return result[0]['count']

    def register_user(self, user_dict):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value, data=user_dict,
                                          primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def delete_user(self, user_id):
        user_dict = {
            SQL_CONSTS.UsersColumns.REGISTRATION_STATUS.value: SQL_CONSTS.REGISTRATION_STATUS_TYPES.DELETED.value,
            SQL_CONSTS.UsersColumns.FIREBASE_UID.value: user_id,
            SQL_CONSTS.UsersColumns.UPDATE_DATE: time.time()}
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS.value, data=user_dict,
                                          primary_key=SQL_CONSTS.UsersColumns.FIREBASE_UID.value)

    def create_users_fr_table(self):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'Create Table public.{SQL_CONSTS.TablesNames.USERS_FR_DATA.value} ('
                               f'{SQL_CONSTS.UsersFrDataColumns.USER_ID.value} varchar, '
                               f'{SQL_CONSTS.UsersFrDataColumns.FR_DATA.value} bytea, '
                               f'primary key ({SQL_CONSTS.UsersFrDataColumns.USER_ID.value}) '
                               f');')

    def get_unanalyzed_images_by_uid(self, user_id):
        sql_query = f'SELECT * from {SQL_CONSTS.TablesNames.IMAGES.value} WHERE ' \
                    f'{SQL_CONSTS.ImageColumns.USER_ID}=%s and {SQL_CONSTS.ImageColumns.ANALYZED_IMAGE_TS.value} is null'
        data = (user_id,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                return results

    def update_users_fr_data(self, users_fr_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USERS_FR_DATA.value, data=users_fr_data,
                                          primary_key=SQL_CONSTS.UsersFrDataColumns.USER_ID.value)

    def update_images_analyzed(self, user_id, filenames, timestamp):
        sql_query = f'UPDATE {SQL_CONSTS.TablesNames.IMAGES.value} SET {SQL_CONSTS.ImageColumns.ANALYZED_IMAGE_TS.value}=%s ' \
                    f'WHERE {SQL_CONSTS.ImageColumns.USER_ID}=%s and {SQL_CONSTS.ImageColumns.FILENAME.value} in %s'
        data = (timestamp, user_id, tuple(filenames))
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)

    def create_dreambooth_requests_table(self):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(

                    f'CREATE TABLE {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS} ('
                    f' {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID} SERIAL PRIMARY KEY,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ARGS} varchar not null,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.USER_ID} varchar not null,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.IS_PREMIUM} varchar,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START} double precision,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_END} double precision,'
                    f'{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_TYPE} varchar'
                    f');')

    def post_dreambooth_request(self, request_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value,
                                          data=request_data,
                                          primary_key=SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value)

    def get_latest_user_dreambooth_request(self, user_id):
        # select * from dreambooth_requests where request_start is null or (request_end is null and request_start<8) order by is_premium,request_id
        # select * from dreambooth_requests order by request_start desc
        sql_query = f'select * from {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} where {SQL_CONSTS.DreamboothRequestsColumns.USER_ID.value} = %s order by {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} desc limit 1'
        data = (user_id,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
                if results is None or len(results) == 0:
                    return None
                results = [dict(result) for result in results]
                return results[0]

    def get_user_dreambooth_completed_requests(self, user_id):
        # select * from dreambooth_requests where request_start is null or (request_end is null and request_start<8) order by is_premium,request_id
        # select * from dreambooth_requests order by request_start desc
        sql_query = f'select * from {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} where {SQL_CONSTS.DreamboothRequestsColumns.USER_ID.value} = %s and {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_RESULT.value} is not null and ({SQL_CONSTS.DreamboothRequestsColumns.REQUEST_STATUS.value} <> \'{SQL_CONSTS.MISC_SERVER_CONSTS.DREAMBOOTH_REQUEST_STATUS_DELETED.value}\' or {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_STATUS.value} is null) order by {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} desc'
        data = (user_id,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
                if results is None or len(results) == 0:
                    return None
                results = [dict(result) for result in results]
                return results

    def delete_dreambooth_request(self,user_id, request_id):
        sql_query = f'update {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} set {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_STATUS.value}=%s where {SQL_CONSTS.DreamboothRequestsColumns.USER_ID.value} = %s and {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value} = %s'
        data = (SQL_CONSTS.MISC_SERVER_CONSTS.DREAMBOOTH_REQUEST_STATUS_DELETED.value,user_id,request_id)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
        return

#TODO remove this
    def time_estimate_for_user_request(self, user_id, max_time_process_in_seconds=60 * 40,
                                       request_processing_time_in_seconds=60 * 30):
        '''
        This method goes over all the requests which were not started/took too much time, and evaluates when a request will be ready.


        select * from dreambooth_requests where request_start is null or (request_end is null and request_start<8) order by is_premium,request_id
        '''
        time_considered_error = time.time() - max_time_process_in_seconds
        sql_query = f'select * from {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} where {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} is null or ({SQL_CONSTS.DreamboothRequestsColumns.REQUEST_END.value} is null and {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value}<%s) order by {SQL_CONSTS.DreamboothRequestsColumns.IS_PREMIUM.value},{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value} '
        data = (time_considered_error,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
                if results is None or len(results) == 0:
                    return 0
                results = [dict(result) for result in results]
                num_people_before_user = 0
                process_latest_start = 0
                for result in results:
                    if result[SQL_CONSTS.DreamboothRequestsColumns.USER_ID.value] == user_id:
                        break
                    if result[SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value] is not None:
                        process_latest_start = max(process_latest_start,
                                                   result[SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value])

                    else:
                        num_people_before_user += 1
                time_estimate = request_processing_time_in_seconds * num_people_before_user
                if process_latest_start != 0:
                    time_estimate += request_processing_time_in_seconds - (time.time() - process_latest_start)
                return time_estimate


    def num_users_before_user_request(self, user_id, max_time_process_in_seconds=60 * 40,):
        '''
        This method goes over all the requests which were not started/took too much time, and evaluates when a request will be ready.


        select * from dreambooth_requests where request_start is null or (request_end is null and request_start<8) order by is_premium,request_id
        '''
        time_considered_error = time.time() - max_time_process_in_seconds
        sql_query = f'select * from {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} where {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} is null or ({SQL_CONSTS.DreamboothRequestsColumns.REQUEST_END.value} is null and {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value}<%s) order by {SQL_CONSTS.DreamboothRequestsColumns.IS_PREMIUM.value},{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value} '
        data = (time_considered_error,)
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql_query, data)
                results = cursor.fetchall()
                if results is None or len(results) == 0:
                    return 0
                results = [dict(result) for result in results]
                num_people_before_user = 0
                user_request_found = False
                for result in results:
                    if result[SQL_CONSTS.DreamboothRequestsColumns.USER_ID.value] == user_id:
                        user_request_found = True
                        break
                    num_people_before_user += 1
                if not user_request_found:
                    return 0
                return num_people_before_user

    def get_next_dreambooth_request_to_process(self, update_start_time=True, max_time_process_in_seconds=60 * 45):
        '''
        select * from dreambooth_requests where request_start is null or (request_end is null and request_start<8) order by is_premium,request_id
        '''
        time_considered_error = time.time() - max_time_process_in_seconds
        sql_query = f'select * from {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} where {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} is null or ({SQL_CONSTS.DreamboothRequestsColumns.REQUEST_END.value} is null and {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value}<%s) order by {SQL_CONSTS.DreamboothRequestsColumns.IS_PREMIUM.value},{SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID} limit 1'
        data = (time_considered_error,)
        with self.get_connection(autocommit=False) as connection:
            with connection.cursor() as cursor:
                cursor.execute("BEGIN")
                cursor.execute(sql_query, data)
                first_result = cursor.fetchone()
                if first_result is None: return None
                result = dict(first_result)
                request_id = result[SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value]
                update_command = f'update {SQL_CONSTS.TablesNames.DREAMBOOTH_REQUESTS.value} set {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_START.value} = %s where {SQL_CONSTS.DreamboothRequestsColumns.REQUEST_ID.value} = %s'
                update_data = (time.time(), request_id)
                if update_start_time:
                    cursor.execute(update_command, update_data)
                cursor.execute('COMMIT')
                return result
