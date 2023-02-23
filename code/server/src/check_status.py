import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
table = dynamodb.Table('Models')

def check_train_status(event, context):
    job_name = event['job_name']
    sagemaker = boto3.client(service_name='sagemaker', region_name="us-east-1")
    status_codes = {
        'InProgress': 'IN_PROGRESS',
        'Completed': "SUCCESS",
        'Failed': 'FAILED'
    }
    # confirm that the training job has started
    res = sagemaker.describe_training_job(TrainingJobName=job_name)['TrainingJobStatus']
    cstatus = status_codes[res]
    res = table.query(KeyConditionExpression=Key('name').eq(event['job_name']))   
    if res and 'Items' in res and res['Items']:
        item = res['Items'][0]
        response = table.update_item(
        Key={'name': item['name'], 'timestamp': item['timestamp']},
        UpdateExpression="set cstatus=:s",
        ExpressionAttributeValues={':s': cstatus},
        ReturnValues="UPDATED_NEW")
        cstatus = cstatus
    return {
        'job_name': event['job_name'],
        'statusCode': 200,
        'body': json.dumps('Train job status'),
        'cstatus': cstatus
    }

def check_deplyment_status(event, context):
    job_name = event['job_name']
    endpoint_name = event['endpoint_name']
    sagemaker = boto3.client(service_name='sagemaker')
    status_codes = {
        'Creating': 'IN_PROGRESS',
        'InService': "DEPLOYED",
        'Failed': 'FAILED'
    }
    # confirm that the training job has started
    res = sagemaker.describe_endpoint(EndpointName=endpoint_name)['EndpointStatus']
    cstatus = status_codes[res]
    res = table.query(KeyConditionExpression=Key('name').eq(job_name))   
    if res and 'Items' in res and res['Items'] and cstatus == 'DEPLOYED':
        item = res['Items'][0]
        response = table.update_item(
        Key={'name': item['name'], 'timestamp': item['timestamp']},
        UpdateExpression="set cstatus=:s",
        ExpressionAttributeValues={':s': cstatus},
        ReturnValues="UPDATED_NEW")

    return {
        'statusCode': 200,
        'job_name': event['job_name'],
        'body': json.dumps('Checking endpoint deployment!'),
        'endpoint_name': endpoint_name,
        'cstatus': cstatus
    }
