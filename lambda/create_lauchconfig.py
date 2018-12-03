# -*- coding: utf-8 -*-

import boto3
import json
import os
import logging

import time
from datetime import datetime as dt

# Lambdaの環境変数
ssm_ami       = os.environ['SSM_AMI']
ssm_lc        = os.environ['SSM_LC']
iam_role      = os.environ['IAM_ROLE']
keypair       = os.environ['KEYPAIR']
instance_type = os.environ['INSTANCE_TYPE']
pre_lc_name   = os.environ['PRE_LC_NAME']
sg_id         = os.environ['SG_ID']

exec_time     = dt.now().strftime('%Y%m%d%H%M')
ssm_client    = boto3.client('ssm')
lc_client     = boto3.client('autoscaling')
code_pipeline = boto3.client('codepipeline')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda実行
def lambda_handler(event, context):
    result = modify_ssm_lc()
    if result == 0:
        logger.info('Lambdaの処理が正常終了しました。')
        code_pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
    else:
        logger.error('Lambdaの処理が失敗しました。')
        code_pipeline.put_job_failure_result(
            jobId=event['CodePipeline.job']['id'],
            failureDetails={
                'type': 'JobFailed',
                'message': '異常終了'
        )

# AMI_IDをSSMパラメータストアから取得
def get_ami_id():
    try:
        ssm_get_value = ssm_client.get_parameters(
            Names = [ssm_ami]
            )['Parameters'][0]['Value']
        logger.info('起動設定のAMIは' + ssm_get_value + 'です。')
        return ssm_get_value
    except:
        logger.error('SSMのパラメータ取得に失敗しました')
        return 1

# Launchconfig作成
def create_launchconfig():
    ami_id = get_ami_id()
    if ami_id != 1:
        try:
            update_lc_name = pre_lc_name + '_' + exec_time
            create_lc = lc_client.create_launch_configuration(
                IamInstanceProfile=iam_role,
                ImageId=ami_id,
                KeyName=keypair,
                InstanceType=instance_type,
                LaunchConfigurationName=update_lc_name,
                SecurityGroups=[sg_id]
                )
            logger.info('作成した起動設定は' + update_lc_name + 'です。')
            return update_lc_name
        except:
            logger.error('起動設定の作成に失敗しました。')
            return 1
    else:
        return 1

# SSMパラメータのLaunchconfigを変更
def modify_ssm_lc():
    update_ssm_lc = create_launchconfig()
    if update_ssm_lc != 1:
        try:
            put_ssm = ssm_client.put_parameter(
                Name  = ssm_lc,
                Value = update_ssm_lc,
                Type  = 'String',
                Overwrite=True
                )
            return 0
        except:
            logger.info('SSMパラメータの更新に失敗しました。')
            return 1
    else:
        return 1
