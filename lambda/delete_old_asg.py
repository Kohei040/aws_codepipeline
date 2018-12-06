# -*- coding: utf-8 -*-

import boto3
import json
import os
import logging

import time
from datetime import datetime as dt

# Lambdaの環境変数
ssm_old_asg  = os.environ['SSM_OLD_ASG']

exec_time     = dt.now().strftime('%Y%m%d%H%M')

ssm_client    = boto3.client('ssm')
asg_client    = boto3.client('autoscaling')
code_pipeline = boto3.client('codepipeline')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda実行
def lambda_handler(event, context):
    result = delete_asg()
    logger.info(result)

    # CodePipelineへ結果を通知
    if result == 0:
        logger.info('Lambda terminated normally')
        code_pipeline.put_job_success_result(jobId=event['CodePipeline.job']['id'])
    else:
        logger.error('Lambda terminated abnormally')
        code_pipeline.put_job_failure_result(
            jobId=event['CodePipeline.job']['id'],
            failureDetails={
                'type': 'JobFailed',
                'message': 'Abnormally'
            }
        )

# 旧AutoScalingGroupをSSMパラメータストアから取得
def get_old_autoscaling():
    try:
        get_ssm_old_asg = ssm_client.get_parameters(
            Names = [ssm_old_asg]
            )['Parameters'][0]['Value']
        logger.info('Old AutoScalingGroup is ' + get_ssm_old_asg)
        return get_ssm_old_asg
    except Exception as e:
        logger.error('SSM parameter aquisition failed\n' + str(e))
        return 1

# 旧AutoScalingGrooup削除
def delete_asg():
    old_asg = get_old_autoscaling()
    if old_asg != 1:
        try:
            asg_client.delete_auto_scaling_group(
                AutoScalingGroupName = old_asg
            )
            return 0
        except Exception as e:
            logger.error('Failed to delete old AutoScalingGroup \n' + str(e))
            return 1
    else:
        return 1

