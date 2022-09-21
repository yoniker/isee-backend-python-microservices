from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

purchase_token = 'bkjmmmcpbkonbgjlkcdbfggg.AO-J1OwrJOO4Un0vRXEiLQCp_jcfgcc7dLiOU_eijdPpS0piAEPb04NX2do8PJthy9TdMgKNewuqC-K5lMLa-a9Pa4BJ9SjrSBTU6Gq0bGvRESPc4YoLEc4'
#purchase_token = 'pnokbbkckefmadldfcndomkb.AO-J1Ozb464f18zpcYzvvsg6VPoM2UOcgzh6AuudGb7ywvIGQH3pvPWJLxsTFaPT2zEC1Wsp2Jlpva2pHlGQ4JpEhFik9FUNGPaxYYsrGpD5oe_XKCr0SQw'
credentials = ServiceAccountCredentials.from_json_keyfile_name('isee.json')
service = build('androidpublisher','v3',credentials=credentials)
google_request = service.purchases().subscriptions().get(packageName='com.voiladating.FaceAnalyzer',subscriptionId='isee_monthly_17_sep_2022',token=purchase_token)
response = google_request.execute()
print(response)

#service.close()