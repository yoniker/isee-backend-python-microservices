import boto3


s3 = boto3.client('s3')
s3.download_file('com.voiladating.users', 'demo_images/elon.jpg', 'haha1.jpg')