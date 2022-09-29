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
def create_token(purchase_token,subscription_id):
    expire_token_time = time.time() + 60 * 2  # 60*60*24
    iSee_data = {
            'expiry':expire_token_time, #expire in 24 hours
            'premium':True,
            'purchase_token':purchase_token,
            'subscription_id':subscription_id
        }
    iSee_token = fernet.encrypt(json.dumps(iSee_data).encode('utf-8')).decode('utf-8')
    return iSee_token