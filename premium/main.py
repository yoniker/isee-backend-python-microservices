from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

purchase_token = 'hjknglhcdbahjgpfejinpnda.AO-J1OzSMqQrg92jraorcXq3vwJrPPAcFw55500t2exw1stcKyC1gd60TIXymFfYKQ7QuUCs2qqXZgq8_PbqSoZT125DoHVQ3IYLYzRsgK_zIGZqI9YnkZA'
subscriptionId = 'isee_weekly_17_sep_2022'

credentials = ServiceAccountCredentials.from_json_keyfile_name('isee.json')
service = build('androidpublisher','v3',credentials=credentials)
google_request = service.purchases().subscriptions().get(packageName='com.voiladating.FaceAnalyzer',subscriptionId=subscriptionId,token=purchase_token)
response = google_request.execute()
print(response)

#service.close()