import json
import pyodbc
import boto3
import os
import pandas as pd
import openpyxl

SQL_CONNECTION = os.environ.get('SQL_CONNECTION')
SQL_PROC = os.environ.get('SQL_PROC')
FILE_NAME = os.environ.get('FILE_NAME')
BUCKET_NAME = os.environ.get('BUCKET_NAME')


def get_connection_string_from_parameter_store():
    lambda_client = boto3.client('lambda')
    lambda_client_parameter = {"Name": SQL_CONNECTION}
    lambda_response = lambda_client.invoke(FunctionName="getParameterStoreValue", InvocationType='RequestResponse',
                                           Payload=json.dumps(lambda_client_parameter))
    return json.load(lambda_response['Payload'])


def get_sql_connection():
    sql_connection_string = get_connection_string_from_parameter_store()
    sql_connection = pyodbc.connect(sql_connection_string)
    sql_query = f'EXEC {SQL_PROC}'
    return sql_connection, sql_query


def excel_export(df):
    df.to_excel(FILE_NAME, index=False)


def data_clean(df):
    df.replace(['\r', '\n'], ' ', regex=True, inplace=True)
    df.replace(r'\s+', ' ', regex=True, inplace=True)
    df.replace(['\u001e', '\u001f'], ' ', regex=True, inplace=True)
    return df


def s3_upload():
    s3 = boto3.client('s3')
    s3.upload_file('/tmp/' + FILE_NAME, BUCKET_NAME, FILE_NAME)


def sql_query_and_excel_export():
    sql_connection, sql_query = get_sql_connection()
    df = pd.read_sql_query(sql_query, sql_connection)
    df = data_clean(df)
    excel_export(df)
    s3_upload()


def handle_errors(action):
    try:
        return action()
    except Exception as e:
        print(f'Error: {e}')
        raise


def lambda_handler(event, context):
    handle_errors(lambda: sql_query_and_excel_export())
