import boto3
from botocore.exceptions import ClientError
import logging
import os
import botocore

REAL_BUCKET = 'com.voiladating.users2'
CELEBS_BUCKET = 'com.voiladating.celebs'


def generate_users_presigned_url(aws_key, bucket_name=REAL_BUCKET, expiresIn=60, region_name='us-east-1'):
    s3_client = boto3.client('s3', region_name=region_name)
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': aws_key},
        ExpiresIn=expiresIn)


def get_celeb_image_url(celeb_name, filename):
    # /celeb_image/Jackie Chan/1.jpeg
    s3_client = boto3.client('s3')
    object_key = f'{celeb_name}/{filename}'
    presigned_url = s3_client.generate_presigned_url('get_object', Params={'Bucket': CELEBS_BUCKET, 'Key': object_key})
    return presigned_url


def upload_file_to_s3(file_name, bucket=REAL_BUCKET, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except botocore.exceptions.ClientError as e:
        logging.error(e)
        return False
    return True


def download_file_from_s3(filename, object_name, bucket=REAL_BUCKET):
    try:
        s3 = boto3.client('s3')
        with open(filename, 'wb') as f:
            s3.download_fileobj(bucket, object_name, f)
            return True
    except:
        return False