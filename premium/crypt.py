import json
from cryptography.fernet import Fernet
import time

with open('iSee_symmetric_key.key','rb') as f:
    key = f.read()
fernet = Fernet(key)

def validate_token(token:str):
    try:
        token = token.encode('utf-8') #convert to bytes
        result = fernet.decrypt(token)
        result = json.loads(result)
        if result['premium'] == True and result['expiry'] > time.time():
            return True
        return False
    except:
        print('error decrypting token. returning False')
        return False

def encrypt(data:dict):
    return fernet.encrypt(json.dumps(data).encode('utf-8')).decode('utf-8')