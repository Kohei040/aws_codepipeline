# -*- coding: utf-8 -*-

import boto3
import json
import os
import logging

import time
from datetime import datetime as dt

exec_time = dt.now().strftime('%Y%m%d%H%M')
ssm_client = boto3.client('ssm')
lc = boto3.client('autoscaling')
code_pipeline = boto3.client('codepipeline')

ssm_ami_name  = os.environ['SSM_AMI_NAME']
ssm_lc_name   = os.environ['SSM_LC_NAME']
iam_role  = os.environ['IAM_ROLE']
instance_type = os.environ['INSTANCE_TYPE']
lc_name = os.environ['LC_NAME']
sg_id   = os.environ['SG_ID']

# Lambda実行
def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    result = modify_ssm_lc()
    if result == 0:
        logger.info('Lambdaの処理が正常終了しました。')
        code_pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
    else:
        logger.error('Lambdaの処理に失敗しました。')
        code_pipeline.put_job_failure_result(jobId=event['CodePipeline.job']['id'])

# AMI_IDをSSMパラメータストアから取得
def get_ami_id():
    try:
        ssm_get_value = ssm_client.get_parameters(
            Names = [ssm_ami_name]
            )['Parameters'][0]['Value']
        print('起動設定のAMIは' + ssm_get_value + 'です。')
        return ssm_get_value
    except:
        print("SSMのパラメータ取得に失敗しました")
        return 1

# Launchconfig作成
def create_launchconfig():
    ami_id = get_ami_id()
    update_lc_name = lc_name + '_' + exec_time
    create_lc = lc.create_launch_configuration(
        IamInstanceProfile=iam_role,
        ImageId=ami_id,
        InstanceType=instance_type,
        LaunchConfigurationName=update_lc_name,
        SecurityGroups=[sg_id]
    )
    print('作成した起動設定は' + update_lc_name + 'です。')
    return update_lc_name

# SSMパラメータのLaunchconfigを変更
def modify_ssm_lc():
    update_ssm_lc = create_launchconfig()
    try:
        put_ssm = ssm_client.put_parameter(
            Name  = ssm_lc_name,
            Value = update_ssm_lc,
            Type  = 'String',
            Overwrite=True
            )
        return 0
    except:
        return 1
