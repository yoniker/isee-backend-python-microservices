import os
import psycopg2
import requests
from flask import Flask,jsonify,request
import time
import random
from postgres_client import PostgresClient
import numpy as np
import pickle
import json
from sql_consts import SQL_CONSTS
from server_consts import ServerConsts
import geopy
from functools import partial
import pandas as pd
import boto3
from multiprocessing.pool import ThreadPool
from datetime import datetime
import logging
from botocore.exceptions import ClientError
import os


app = Flask(__name__)

@app.route('/user_data/analyze_custom_image/<path:f>')
def analyze_custom_face_image(f):
    print(f'path is {f}')
    return jsonify({'f':f'{f}'})



if __name__ == '__main__':
   app.run(threaded=True,port=20003,host="0.0.0.0",debug=False)


