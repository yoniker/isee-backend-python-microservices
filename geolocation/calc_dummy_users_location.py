import psycopg2
import time
import pandas as pd
import requests
from sql_consts import SQL_CONSTS
import geopy.distance
from sqlalchemy import create_engine
from random import uniform

# host = os.getenv('RD_HOST_NAME')or 'db.ck82h9f9wsbf.us-east-1.rds.amazonaws.com'

connect_str_papush = f"dbname='pof' user='yoni' host='192.116.48.67' " + \
                     "password='dor'"
postgres_conn = psycopg2.connect(connect_str_papush)


# def newpoint():
#    return  uniform(-90, 90),uniform(-180,180)


# while True:
#     lat,lon = newpoint()
#     with postgres_conn.cursor() as cursor:
#         cursor.execute(f'select count(*) from   aws_users z where  earth_distance(ll_to_earth(z.latitude, z.longitude), ll_to_earth({lat}, {lon})) < 100000.0')
#         results = cursor.fetchall()
#         if results[0][0] > 10000:
#             with open('places.txt','a') as f:
#                 f.write(f'{lat} {lon}\n')
#             print(f'{lat} {lon}\n')



class Region:
    def __init__(self, region_name,region_index, lat, lon, radius_in_km=100):
        self.region_name = region_name
        self.lat = lat
        self.lon = lon
        self.radius_in_km = radius_in_km
        self.region_index = region_index
        
    def __repr__(self):
        return self.region_name+' Region '+f'{self.lat},{self.lon}'
        
    def point_belongs_to_region(self,lat,lon):
        try:
            point_location = (lat, lon)
            if any([x is None for x in [self.lat,self.lon,lat,lon]]): return False
            return geopy.distance.distance((self.lat, self.lon), point_location).km <= self.radius_in_km
        
        except:
            return None
        

regions_data = {'Toronto':(43.667258,-79.389090),
           'NYC': (40.72976510959369, -74.03903341041173),
           'Haifa': (32.798746018428766, 34.996495542328404),
           'Ottawa': (45.43065490304358, -75.68811248593178),
           'Montreal': (45.56385604756384, -73.66305420910956),
           'Rio de Janeiro':(-22.89771341096221, -43.34127074658475),
           'London':(51.485596723879375, -0.1262711693136139),
           'Louisiana':(31.69264533644187,-91.69515100573798),
           'Springfield':(41.99530745019607, -71.95695561747344),
           'Washington':(39.180425911024116,-75.7646572520419),
           'Halifax':(36.71984590850663,-78.71158093936724),
           'Austin':(31.816312924067034,-100.04751436446828),
           'Oklahoma':(34.4693467212535,-96.73303803865925),
           'Nashville':(35.900856405195455,-85.9219655209869),
           'Louisville':(38.594249095225884, -84.8057265595222),
           'Charlotte':(35.30548791350094,-79.07007118495751),
           'Arkansas':(34.632944464494514,-91.85770174145335),
           'Pennsylvania':(40.93254360170596,-76.8771452468818)}


regions = [Region(region_name=region_name,region_index=region_index, lat=region_location[0], lon=region_location[1],) for region_index, (region_name, region_location) in enumerate(regions_data.items(),start=1)]
engine = create_engine('postgresql://yoni:dordordor@voila-postgres-db.ck82h9f9wsbf.us-east-1.rds.amazonaws.com/pof')
print('reading from local')
aws_users_table = pd.read_sql_query('select * from aws_users2', postgres_conn)
print('saving to AWS...')
aws_users_table.to_sql(name='aws_users2',con=engine)
# aws_users_table.to_sql(name='aws_users2',con=engine)
# def calc_user_region(user_data):
#     user_lat,user_lon = user_data.latitude,user_data.longitude
#     for region in regions:
#         if region.point_belongs_to_region(lat=user_lat,lon=user_lon):
#             return region.region_index
#     return 0
# aws_users_table['region_index'] = aws_users_table.apply(calc_user_region,axis=1)
# from sqlalchemy import create_engine
# engine = create_engine('postgresql://yoni:dor@localhost/pof')
# aws_users_table.to_sql(name='aws_users2',con=engine)
#engine = create_engine('mysql+pymysql://scott:tiger@localhost/foo')
#postgres_engine = create_engine("mysql+pymysql://" + 'root' + ":" + 'dordor' + "@" + 'localhost' + "/" + 'pof')


