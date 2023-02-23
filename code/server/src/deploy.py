import json
import time
import boto3
import uuid
from datetime import datetime
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
table = dynamodb.Table('Models')
ssm = boto3.client('ssm', region_name='us-east-1')
role = ssm.get_parameter(Name='/vda/iam/lambdarole')['Parameter']['Value']

def deploy(event, context):
    sage = boto3.Session().client(service_name='sagemaker', region_name="us-east-1") 

    job_name = event['job_name']
    timestamp = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
    model_name=f"{job_name}-model-{timestamp}"
    info = sage.describe_training_job(TrainingJobName=job_name)
    model_data = info['ModelArtifacts']['S3ModelArtifacts']

    #hosting_image = '685385470294.dkr.ecr.eu-west-1.amazonaws.com/image-classification:latest'
    hosting_image = '438346466558.dkr.ecr.eu-west-1.amazonaws.com/linear-learner:latest'
    primary_container = {
        'Image': hosting_image,
        'ModelDataUrl': model_data,
    }
    
    create_model_response = sage.create_model(
        ModelName = model_name,
        ExecutionRoleArn = role,
        PrimaryContainer = primary_container)
        
    timestamp = time.strftime('-%Y-%m-%d-%H-%M-%S', time.gmtime())
    endpoint_config_name = job_name + '-epc' + timestamp
    endpoint_config_response = sage.create_endpoint_config(
        EndpointConfigName = endpoint_config_name,
        ProductionVariants=[{
            'InstanceType':'ml.m4.xlarge',
            'InitialInstanceCount':1,
            'ModelName':model_name,
            'VariantName':'AllTraffic'}])
    endpoint_name = job_name + '-ep' + timestamp
    print('Endpoint name: {}'.format(endpoint_name))
    
    endpoint_params = {
        'EndpointName': endpoint_name,
        'EndpointConfigName': endpoint_config_name,
    }
    endpoint_response = sage.create_endpoint(**endpoint_params)
    
    return {
        'statusCode': 200,
        'job_name': event['job_name'],
        'body': json.dumps('Deploying the endpoint!'),
        'cstatus': 'DEPLOYING',
        'endpoint_name': endpoint_name
    }