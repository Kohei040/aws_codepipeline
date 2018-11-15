# -*- coding: utf-8 -*-

import boto3
import json
import os
import logging

import time
from datetime import datetime as dt

# Lambdaの環境変数
ori_asg_name = os.environ['ASG_NAME']
ssm_lc_name  = os.environ['LAUNCHCONFIG']
min_size     = os.environ['MIN_SIZE']
max_size     = os.environ['MAX_SIZE']
az_1         = os.environ['AZ_1']
az_2         = os.environ['AZ_2']
subnet_1     = os.environ['SUBNET_1']
subnet_2     = os.environ['SUBNET_2']
alb_target   = os.environ['ALB_TARGET']

exec_time  = dt.now().strftime('%Y%m%d%H%M')
ssm_client = boto3.client('ssm')
asg_client = boto3.client('autoscaling')
code_pipeline = boto3.client('codepipeline')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda実行
def lambda_handler(event, context):
    result = create_autoscale()
    if result == 0:
        logger.info('Lambdaの処理が正常終了しました。')
        code_pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
    else:
        logger.error('Lambdaの処理が失敗しました。')
        code_pipeline.put_job_failure_result(jobId=event['CodePipeline.job']['id'])

# 最新のLaunchConfigをSSMパラメータストアから取得
def get_launchconfig():
    try:
        get_ssm_lc = ssm_client.get_parameters(
            Names = [ssm_lc_name]
            )['Parameters'][0]['Value']
        logger.info('起動設定は' + get_ssm_lc + 'です。')
        return get_ssm_lc
    except:
        logger.error('SSMのパラメータ取得に失敗しました。')
        return 1

# AutoScalingGroup作成
def create_autoscale():
    launchconfig = get_launchconfig()
    if launchconfig != 1:
        try:
            asg_name = ori_asg_name + '_' + exec_time
            new_asg = asg_client.create_auto_scaling_group(
                AutoScalingGroupName=asg_name,
                LaunchConfigurationName=launchconfig,
                MinSize=int(min_size),
                MaxSize=int(max_size),
                AvailabilityZones=[
                    az_1,
                    az_2
                    ],
                TargetGroupARNs=[
                    alb_target
                    ],
                HealthCheckType='EC2',
                HealthCheckGracePeriod=60,
                VPCZoneIdentifier=subnet_1 + ',' + subnet_2,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': asg_name,
                    },
                ]
            )
            logger.info('作成したAutoScalingGroupは' + asg_name + 'です。')
            return 0
        except:
            logger.error('AutoScalingGroupの作成に失敗しました。')
            return 1
    else:
        return 1
