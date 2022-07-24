import psycopg2.pool
import psycopg2
from psycopg2.extras import RealDictCursor
from sql_consts import SQL_CONSTS
from psycopg2.errors import UniqueViolation
from contextlib import contextmanager


class PostgresClient:
    def __init__(self,database='real_users',user='yoni',password='dor',host='localhost'):
        self.pool = psycopg2.pool.ThreadedConnectionPool(minconn=1, maxconn=20,
                                                         database=database,
                                                         user=user,
                                                         password=password,
                                                         host=host,
                                                         cursor_factory=RealDictCursor
                                                         )
        self.autocommit = True
    
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
                    print(cursor.mogrify(insert, data))
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
                    print(cursor.mogrify(update, data))
                    cursor.execute(update, data)
    

    def get_location_by_coordinates(self, lat, lon,radius_in_km=2):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                query = f'SELECT * FROM {SQL_CONSTS.TablesNames.UTIL_LOCATION.value} where true ' 
                query_args = []
                query += f' and earth_box(ll_to_earth(%s,%s ),%s*1000/1.609) @> ll_to_earth({SQL_CONSTS.UtilLocationColumns.LATITUDE.value}, {SQL_CONSTS.UtilLocationColumns.LONGITUDE.value}) '
                query_args += [lat,lon,radius_in_km]
                print(f'going to execute the query {cursor.mogrify(query,query_args)}')
                cursor.execute(query, query_args)
                results = cursor.fetchall()
                if len(results) > 0:
                    return dict(results[0])[SQL_CONSTS.UtilLocationColumns.DESCRIPTION.value]
                return ''
    
    def get_location_by_description(self, description):
        with self.get_connection() as connection:
            with connection.cursor() as cursor:
                sql_cmd = f'SELECT * FROM {SQL_CONSTS.TablesNames.UTIL_LOCATION.value} where ' \
                          f' {SQL_CONSTS.UtilLocationColumns.DESCRIPTION} = %s'
                data = (description,)
                cursor.execute(sql_cmd, data)
                results = cursor.fetchall()
                return [dict(result) for result in results]
    
    
    def update_location_data(self, location_data):
        return self._update_table_by_dict(table_name=SQL_CONSTS.TablesNames.UTIL_LOCATION.value, data=location_data,
                                          primary_key=SQL_CONSTS.UtilLocationColumns.PRIMARY_KEY)

    