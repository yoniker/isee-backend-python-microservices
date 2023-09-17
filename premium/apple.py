import requests
import json








def verify_valid_apple_receipt(receipt_data):
    ISEE_APPLE_SHARED_SECRET = '24983c6c10194448ac590a7de4b2533a'

    APPLE_SANDBOX_VERIFICATION_URL = 'https://sandbox.itunes.apple.com/verifyReceipt'

    APPLE_PRODUCTION_VERIFICATION_URL = 'https://buy.itunes.apple.com/verifyReceipt'
    request_body = {

        'password': ISEE_APPLE_SHARED_SECRET,
        'receipt-data': receipt_data,
        'exclude-old-transactions': True

    }
    for apple_verify_url in [APPLE_SANDBOX_VERIFICATION_URL,APPLE_PRODUCTION_VERIFICATION_URL]:
        try:
            response = requests.post(url=apple_verify_url, json=request_body) #TODO there's a ton of information that can and should be saved from the response.
            if json.loads(response.content)['status']==0: #See https://developer.apple.com/documentation/appstorereceipts/responsebody - status ==0 is "ok and not expired", decide what information to take from response
                return True
        except:
            pass
    return False