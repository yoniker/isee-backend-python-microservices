import psycopg2.pool
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_consts import SQL_CONSTS
from psycopg2.errors import UniqueViolation
from contextlib import contextmanager
import time




class PostgresClient:
    def __init__(self,minconn=20,maxconn=200,database='real_users',
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
    def get_connection(self,autocommit=None):
        con = self.pool.getconn()
        con.autocommit = self.autocommit if autocommit is None else autocommit
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
                    cursor.execute(insert, data)
    
        except (psycopg2.errors.NotNullViolation, UniqueViolation) as _:
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



    def create_usage_table(self):
        # taste_mix_ratio double precision,radius double precision,primary key (decider_facebook_id) );
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(f'CREATE TABLE {SQL_CONSTS.TablesNames.USAGE.value} ('
                               f'{SQL_CONSTS.UsageColumns.USER_ID} varchar NOT NULL,'
                               f'{SQL_CONSTS.UsageColumns.CARTOON} varchar,'
                               f'{SQL_CONSTS.UsageColumns.CELEBS_LOOKALIKE} varchar,'
                               f'{SQL_CONSTS.UsageColumns.DREAM_FROM_PROMPT} varchar,'
                               f'{SQL_CONSTS.UsageColumns.DREAM_FROM_IMAGE} varchar,'
                               f'{SQL_CONSTS.UsageColumns.MORPH} varchar,'
                               f'{SQL_CONSTS.UsageColumns.TRAITS} varchar,'
                               
                               f'primary key ({SQL_CONSTS.UsageColumns.USER_ID}) '
                               f');')

    def get_usage_by_id(self, user_id):
        '''
        Get the user's usage details according to the user's id
        :param user_id:
        :return:
        '''
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'select * from {SQL_CONSTS.TablesNames.USAGE.value} where {SQL_CONSTS.UsageColumns.USER_ID.value} = %s'
                data=(user_id,)
                cursor.execute(sql_cmd,data)
                results = cursor.fetchall()
                results = [dict(result) for result in results]
                if len(results) ==0:
                    return None
                return results[0]

    def update_usage_data(self,usage_data):
        self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.USAGE.value,
                                   data=usage_data,
                                   primary_key=SQL_CONSTS.UsageColumns.PRIMARY_KEY.value,)