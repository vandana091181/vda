import re
import boto3
import io
import os
import time
from time import gmtime, strftime
from const import BUCKET_NAME

region = 'us-east-1'

# Define IAM role
ssm = boto3.client('ssm', region_name='us-east-1')
role = ssm.get_parameter(Name='/vda/iam/lambdarole')['Parameter']['Value']

def get_hyperparams_ll(job_name):
    container = '382416733822.dkr.ecr.us-east-1.amazonaws.com/linear-learner:1'
    
    s3 = boto3.client('s3')
    
    training_params = \
    {
        # specify the training docker image
        "AlgorithmSpecification": {
            "TrainingImage": container,
            "TrainingInputMode": "File"
        },
        "RoleArn": role,
        "OutputDataConfig": {
            "S3OutputPath": f's3://{BUCKET_NAME}/sagemaker/DEMO-linear-mnist/output/'
        },
        "ResourceConfig": {
            "InstanceCount": 1,
            "InstanceType": "ml.m4.xlarge",
            "VolumeSizeInGB": 50
        },
        "TrainingJobName": job_name,
        "HyperParameters": {
            "early_stopping_patience":"3",
            "early_stopping_tolerance":"0.001",
            "epochs":"15",
            "feature_dim":"784",
            "loss":"auto",
            "mini_batch_size":"200",
            "normalize_data":"true",
            "normalize_label":"auto",
            "num_models":"auto",
            "optimizer":"auto",
            "predictor_type":"binary_classifier",
            "unbias_data":"auto",
            "unbias_label":"auto",
            "use_bias":"true"
     
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 360000
        },
        "InputDataConfig": [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": f's3://{BUCKET_NAME}/sagemaker/DEMO-linear-mnist/train/',
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "CompressionType": "None"
            },
            {
                "ChannelName": "validation",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": f's3://{BUCKET_NAME}/sagemaker/DEMO-linear-mnist/validation/',
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "CompressionType": "None"
            }
        ]
    }
    
    return training_params
    
    
def get_hyperparams_img(job_name):
    # app_meta = get_app_meta()
    # bucket = app_meta['train_s3_bucket']
    training_image = '811284229777.dkr.ecr.us-east-1.amazonaws.com/image-classification:1'
    num_layers = "18" 
    image_shape = "3,224,224"
    num_training_samples = "10000"
    num_classes = "2"
    mini_batch_size =  "64"
    epochs = "2"
    learning_rate = "0.01"
    training_params = \
    {
        # specify the training docker image
        "AlgorithmSpecification": {
            "TrainingImage": training_image,
            "TrainingInputMode": "File"
        },
        "RoleArn": role,
        "OutputDataConfig": {
            "S3OutputPath": f's3://BUCKET_NAME/ll-data/out/'
        },
        "ResourceConfig": {
            "InstanceCount": 1,
            "InstanceType": "ml.p2.xlarge",
            "VolumeSizeInGB": 50
        },
        "TrainingJobName": job_name,
        "HyperParameters": {
            "image_shape": image_shape,
            "num_layers": str(num_layers),
            "num_training_samples": str(num_training_samples),
            "num_classes": str(num_classes),
            "mini_batch_size": str(mini_batch_size),
            "epochs": str(epochs),
            "learning_rate": str(learning_rate)
        },
        "StoppingCondition": {
            "MaxRuntimeInSeconds": 360000
        },
    #Training data should be inside a subdirectory called "train"
    #Validation data should be inside a subdirectory called "validation"
    #The algorithm currently only supports fullyreplicated model (where data is copied onto each machine)
        "InputDataConfig": [
            {
                "ChannelName": "train",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": f's3://{BUCKET_NAME}/clf-demo/train/',
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "ContentType": "application/x-recordio",
                "CompressionType": "None"
            },
            {
                "ChannelName": "validation",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": f's3://{BUCKET_NAME}/clf-demo/validation/',
                        "S3DataDistributionType": "FullyReplicated"
                    }
                },
                "ContentType": "application/x-recordio",
                "CompressionType": "None"
            }
        ]
    }
    return training_params
    
def get_app_meta():
    ddb = boto3.client('dynamodb', region_name='eu-west-1')
    response = ddb.scan(TableName='AppMeta')
    response['Items'].sort(key = lambda x: x['timestamp'])
    items = []
    for item in response['Items']:
        i = {}
        for k, v in item.items():
            i[k] = list(v.values())[0]
        items.append(i)
    return items[-1]