import json
import time
import boto3
import uuid
from datetime import datetime

import utils as ut

ddb = boto3.client('dynamodb', region_name = 'us-east-1')
sf = boto3.client('stepfunctions', region_name = 'us-east-1')

def execute_train_state_machine(event, context):
  job_name = event['queryStringParameters']['job_name']
  arn =  event['queryStringParameters']['arn']
  response = sf.start_execution(
        stateMachineArn=arn,
        input=json.dumps({"job_name": job_name}),
    )
  print(response)
  try:
      response = json.dumps(response['ResponseMetadata'])
  except:
      pass
  return {
      'statusCode': 200,
      'body': response
  }
def train(job_name):
    # return {
    #     'event': json.dumps(event),
    #     'statusCode': 200,
    #     'cstatus': FAILED
    # }
    
    training_params = ut.get_hyperparams_img(job_name)
    sagemaker = boto3.client(service_name='sagemaker', region_name = 'us-east-1')
    sagemaker.create_training_job(**training_params)
    time.sleep(.5)
    status_codes = {
        'InProgress': 'IN_PROGRESS',
        'Completed': "SUCCESS",
        'Failed': 'FAILED'
    }
    # confirm that the training job has started
    res = sagemaker.describe_training_job(TrainingJobName=job_name)['TrainingJobStatus']
    status = status_codes[res]
    print('Training job current status: {}'.format(status))
    item = {}
    item.update(get_item('name', 'S', event['job_name']))
    item.update(get_item('cstatus', 'S', status_codes[res]))
    item.update(get_item('timestamp', 'S', get_date()))
    item.update(get_item('type', 'S', 'linear'))
    ddb.put_item(TableName='Models', Item=item)  
    return {
        'job_name': event['job_name'],
        'statusCode': 200,
        'body': json.dumps(f'Training job status = {status}'),
        'cstatus': status
    }

def get_item(key, ktype, val):
    return {key: {ktype: val}}
    
def get_date():
    now = datetime.utcnow()
    dt = f'{now.year}-{now.month}-{now.day} {now.hour}:{now.minute}:{now.second}'
    dt = f"{datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')}"
    return dt
    