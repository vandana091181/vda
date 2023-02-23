import json
import boto3
import json


s3 = boto3.client('s3', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

runtime = boto3.Session().client(service_name='runtime.sagemaker', region_name = 'us-east-1') 
sm = boto3.client('sagemaker', region_name='us-east-1')

def detect_vehicle(event, context):
    file_name = event['user']
    s3.download_file('zvissh-us-east-1', file_name, f'/tmp/{file_name}')
    endpoint_name = get_end_point()

    with open(f'/tmp/{file_name}', 'rb') as f:
        payload = f.read()
        payload = bytearray(payload)
    response = runtime.invoke_endpoint(EndpointName=endpoint_name, 
                                       ContentType='application/x-image', 
                                       Body=payload)
    result = response['Body'].read()
    result = json.loads(result)
    
    mask = round(result[1]*100, 2)
    no_mask = round(result[0]*100, 2)
      
    return {
        'statusCode': 200,
        'user': file_name,
        'mask': mask,
        'no_mask': no_mask,
    }

def get_end_point():    
    eps = sm.list_endpoints(SortBy='CreationTime', SortOrder='Descending')['Endpoints']
    eps2 = list(filter(lambda x: 'FMD-1' in x['EndpointName'], eps))
    return eps2[0]['EndpointName']