import os
from enum import Enum
from flask import Flask,jsonify,request
import geopy
from sql_consts import SQL_CONSTS
from postgres_client import PostgresClient


class EnvConsts(str, Enum):
    GOOGLE_API_KEY = 'GOOGLE_API_KEY'
    POSTGRES_USERNAME = 'POSTGRES_USERNAME'
    POSTGRES_PASSWORD = 'POSTGRES_PASSWORD'
    POSTGRES_DB = 'POSTGRES_DB'
    POSTGRES_HOST = 'POSTGRES_HOST'
    
class ResponseConsts(str, Enum):
    LOCATION_DESCRIPTION = 'location_description'
    
    
app = Flask(__name__)
def _get_name_by_locality_desc(address, description):
    try:
        return [x for x in address if description in x['types']][0]['long_name']
    except:
        return ''


def _get_locality_name(address):
    for locality_desc in ['locality', 'administrative_area_level_3', 'administrative_area_level_2',
                          'administrative_area_level_1']:
        
        desc = _get_name_by_locality_desc(address=address, description=locality_desc)
        if len(desc) > 0:
            return desc
    return ''
    
google_api_key = os.environ.get(EnvConsts.GOOGLE_API_KEY.value) or 'AIzaSyDLhAORsJMs32yd0TSMmyNCrueuULDskaE'  # TODO remove this private key completely from codebase
postgres_username = os.environ.get(EnvConsts.GOOGLE_API_KEY.value) or 'yoni'
postgres_password = os.environ.get(EnvConsts.POSTGRES_PASSWORD.value) or 'dordordor'
postgres_db = os.environ.get(EnvConsts.POSTGRES_DB.value) or 'dummy_users'
postgres_host = os.environ.get(EnvConsts.POSTGRES_HOST.value) or 'voila-aurora-cluster.cluster-ck82h9f9wsbf.us-east-1.rds.amazonaws.com'
_geolocator = geopy.geocoders.GoogleV3(api_key=google_api_key)
postgres_client = PostgresClient(database=postgres_db,user=postgres_username,password=postgres_password,host=postgres_host)


@app.route('/geolocation/description_by_coordinates')
def location_description_by_coordinates():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        lat, lon = float(lat.replace(',','')), float(lon.replace(',',''))
        location_description_from_db = postgres_client.get_location_by_coordinates(lat=lat, lon=lon)
        if len(location_description_from_db) > 0:
            print('Getting description from DB, do\'nt need to Apply Google API')
            return jsonify({ResponseConsts.LOCATION_DESCRIPTION.value:location_description_from_db})
        coordinates = f'{lat},{lon}'
        location = _geolocator.reverse(coordinates)
        if location is None:
            return jsonify({ResponseConsts.LOCATION_DESCRIPTION.value:''})
        location_data = location.raw
        address = location_data['address_components']
        # 1.Find the city
        city = _get_locality_name(address=address)
        country = _get_name_by_locality_desc(address=address, description='country')
        location_description_from_google = f'{city}, {country}' if len(country) > 0 else ''
        data_location = {
            SQL_CONSTS.UtilLocationColumns.DESCRIPTION.value: location_description_from_google,
            SQL_CONSTS.UtilLocationColumns.LONGITUDE.value: lon,
            SQL_CONSTS.UtilLocationColumns.LATITUDE.value: lat
        }
        postgres_client.update_location_data(data_location)
        return jsonify({ResponseConsts.LOCATION_DESCRIPTION.value:location_description_from_google})
    except:
       return jsonify({ResponseConsts.LOCATION_DESCRIPTION.value: ''})
    
@app.route('/geolocation/description_by_coordinates/<location_description>')
def coordinates_by_location_description(location_description):
    location_coordinates_from_db = postgres_client.get_location_by_description(description=location_description)
    if len(location_coordinates_from_db) > 0:
        first_location_found = location_coordinates_from_db[0]
        return first_location_found
    location = _geolocator.geocode(location_description)
    if location is not None:
        lon = location.longitude
        lat = location.latitude
        data_location = {
            SQL_CONSTS.UtilLocationColumns.DESCRIPTION.value: location_description,
            SQL_CONSTS.UtilLocationColumns.LONGITUDE.value: lon,
            SQL_CONSTS.UtilLocationColumns.LATITUDE.value: lat
        }
        postgres_client.update_location_data(data_location)
        return data_location
    return None
    
# 'lat': -1.738536480291502, 'lng': 15.1438385197085 = (-1.738536480291502,15.1438385197085) eg latitue appears before longtitude
'''
query to get all users within a certain radius:


select *
from   aws_users z
where  earth_distance(ll_to_earth(z.lat, z.lon), ll_to_earth(32.78929068200862, 34.99529094283844)) < 1000000.0;

see more at
https://stackoverflow.com/questions/43631978/how-to-search-in-a-radius-using-postgres-extension
'''

@app.route('/geolocation/healthcheck')
def say_healthy():
    return jsonify({'status':'geolocation service is up and running'})

if __name__ == '__main__':
   app.run(threaded=True,port=20004,host="0.0.0.0",debug=False)


'''
40.67353669491746, -74.1362361690617 -NYC
curl "localhost:20004/geolocation/description_by_coordinates?lat=40.67353669491746&lon=-74.1362361690617"
40.673268153526806, -74.14229799378738
curl "localhost:20004/geolocation/description_by_coordinates?lat=19.707070&lon=-99.061164"
, 

CREATE INDEX 
   distance_index_for_utils ON util_location USING gist (ll_to_earth(latitude, longitude))

docker build . -t geolocation
docker run -d -it -p  20004:20004/tcp geolocation:latest
'''