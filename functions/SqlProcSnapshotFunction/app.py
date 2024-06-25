import json
import pyodbc
import boto3
import os

SQL_CONNECTION = os.environ.get('SQL_CONNECTION')
SQL_PROC = os.environ.get('SQL_PROC')


def get_connection_string_from_parameter_store():
    lambda_client = boto3.client('lambda')
    lambda_client_parameter = {"Name": SQL_CONNECTION}
    lambda_response = lambda_client.invoke(FunctionName="getParameterStoreValue", InvocationType='RequestResponse',
                                           Payload=json.dumps(lambda_client_parameter))
    return json.load(lambda_response['Payload'])


def sql_call_snapshot_procedure():
    sql_connection_string = get_connection_string_from_parameter_store()
    sql_connection = pyodbc.connect(sql_connection_string)
    sql_cursor = sql_connection.cursor()
    sql_query = f'EXEC {SQL_PROC}'
    sql_cursor.execute(sql_query)
    sql_connection.commit()


def handle_errors(action):
    try:
        return action()
    except Exception as e:
        print(f'Error: {e}')
        raise


def lambda_handler(event, context):
    handle_errors(lambda: sql_call_snapshot_procedure())
