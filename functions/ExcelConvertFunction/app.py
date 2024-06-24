import os
import boto3
import pandas as pd
import openpyxl

s3_bucket = os.environ.get('BUCKET_NAME')
file_name_csv = os.environ.get('FILENAME_IMPORT')
file_name_xlsx = os.environ.get('FILENAME_EXPORT')


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=s3_bucket, Key=file_name_csv)
    df = pd.read_csv(response['Body'])
    df.replace(['\r', '\n'], ' ', regex=True, inplace=True)
    df.replace(r'\s+', ' ', regex=True, inplace=True)
    df.replace(['\u001e', '\u001f'], ' ', regex=True, inplace=True)
    df.to_excel('/tmp/' + file_name_xlsx, index=False)
    s3.upload_file('/tmp/' + file_name_xlsx, s3_bucket, file_name_xlsx)
