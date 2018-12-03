# -*- coding: utf-8 -*-

import boto3
import json
import os
import logging

import time
from datetime import datetime as dt

# Lambdaの環境変数
ori_asg_name = os.environ['ASG_NAME']
ssm_lc_name  = os.environ['SSM_LC']
min_size     = os.environ['MIN_SIZE']
max_size     = os.environ['MAX_SIZE']
az_1         = os.environ['AZ_1']
az_2         = os.environ['AZ_2']
subnet       = os.environ['SUBNET']
alb_target   = os.environ['ALB_TARGET']
ssm_new_asg  = os.environ['SSM_NEW_ASG']
ssm_old_asg  = os.environ['SSM_OLD_ASG']

exec_time  = dt.now().strftime('%Y%m%d%H%M')

ssm_client = boto3.client('ssm')
asg_client = boto3.client('autoscaling')
elb_client = boto3.client('elbv2')
code_pipeline = boto3.client('codepipeline')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda実行
def lambda_handler(event, context):
    result = update_ssm_new_asg()
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
            }
        )

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
            asg_client.create_auto_scaling_group(
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
                VPCZoneIdentifier=subnet,
                Tags=[
                    {
                        'Key': 'Name',
                        'Value': asg_name
                    },
                ]
            )
            logger.info('作成したAutoScalingGroupは' + asg_name + 'です。')
            logger.info('HealthCheckに合格するまで待機します。')

            healthcheck = alb_healthcheck(asg_name)
            logger.info(healthcheck)
            if healthcheck == 0:
                pass
            else:
                raise

            return asg_name
        except:
            logger.error('AutoScalingGroupの作成に失敗しました。')
            return 1
    else:
        return 1

# ALBのHealtcheck確認
def alb_healthcheck(asg_name):
    logger.info('healthcheck' + asg_name)
    try:
        # ASGで起動したインスタンスIDを抽出
        describe_asg = asg_client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[
                asg_name
                ]
            )['AutoScalingGroups'][0]['Instances'][0]['InstanceId']
        instances = describe_asg.split()
        logger.info(instances)

        # ALBのHealtcheckが完了するまで待機
        for instance in instances:
            waiter = elb_client.get_waiter('target_in_service')
            waiter.wait(
                TargetGroupArn=alb_target,
                Targets=[
                    {
                        'Id': instance
                    },
                ]
            )
        return 0
    except:
        logger.info('ALBのHealtcheckに失敗しました。')
        return 1


# SSMパラメータストアの旧AutoScalingGroupを更新
def update_ssm_old_asg():
    try:
        get_old_asg = ssm_client.get_parameters(
            Names = [ssm_new_asg]
            )['Parameters'][0]['Value']
        ssm_client.put_parameter(
            Name  = ssm_old_asg,
            Value = get_old_asg,
            Type  = 'String',
            Overwrite = True
        )
        logger.info('旧AutoScalingGroupは' + get_old_asg + 'です。')
        return 0
    except:
        logger.error('旧AutoScalingGroupの取得に失敗しました。')
        return 1

# SSMパラメータストアの新AutoScalingGroupを更新
def update_ssm_new_asg():
    new_asg = create_autoscale()
    old_asg = update_ssm_old_asg()
    if new_asg != 1 and old_asg == 0:
        try:
            ssm_client.put_parameter(
                Name = ssm_new_asg,
                Value = new_asg,
                Type = 'String',
                Overwrite = True
                )
            logger.info('新AutoScalingGroupは' + new_asg + 'です。')
            return 0
        except:
            logger.error('新AutoScalingGroupのSSM更新に失敗しました。')
            return 1
    else:
        return 1
