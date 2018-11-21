【AWS】AutoSCaling環境でのCI/CD
==============================

# CI/CDの流れ

![CI/CD](https://github.com/Kohei040/aws_code_series_validation/raw/test/image/CICD_Flow.PNG)

1. githubへpush
1. CodePipelineで検知
1. [CodeBuild]AMI作成
    1. CodeBuildの処理をするDockerコンテナを起動
    1. DockerコンテナにPacker&Ansibleインストール
    1. DockerコンテナがPackerの処理を実行
    1. Packerが指定したEC2を起動、Ansibleの処理実行
    1. EC2のAMIを取得、EC2削除
    1. SSMパラメータストアのAMI IDを更新
1. [Lambda]LaunchConfig作成
    1. SSMパラメータストアから最新のAMI IDを取得
    1. LaunchConfig作成
    1. SSMパラメータストアのLaunchConfig名を最新に更新
    1. CodePipelineへジョブの完了を通知
1. [Lambda]AutoScalingGroup作成
    1. SSMパラメータストアから最新のLaunchConfig名を取得
    1. AutoScalingGroup作成
    1. SSMパラメータストアのAutoScalingGroup名の新旧を更新
    1. 新AutoScalingGroupのHeatlhStatusを確認
    1. CodePipelineへジョブの完了を通知
1. [Lambda]Blue/Green deploymnet実施
    1. SSMパラメータストアから新旧のAutoScalingGroup名を取得
    1. ALBに紐づくインスタンスのHealthCheckが全て[healthy]であることを確認
    1. 旧AutoScalingGroupをALBのTargetGroupから削除
    1. CodePipelineへジョブの完了を通知

※2の手順以降は全てCodePipeline上で管理

# Golden AMI作成イメージ

![Create_GoledenAMI](https://github.com/Kohei040/aws_code_series_validation/raw/test/image/Create_Golden_AMI.PNG)

# 各Lambdaの環境変数
- Launchconfig作成用

|Key|Value|
|:--|:--|
|SSM_AMI|ami_id|
|SSM_LC|lc_name|
|INSTANCE_TYPE|t3.micro|
|SG_ID|sg-xxxxxx|
|IAM_ROLE|<作成したRole>|
|PRE_LC_NAME|<LCのPrefix>|

- AutoScalingGroup作成用

|Key|Value|
|:--|:--|
|SSM_NEW_ASG|new_asg|
|SSM_OLD_ASG|old_asg|
|ASG_NAME|<ASGのPrefix>|
|SSM_LC|lc_name|
|ALB_TARGET|<ALBのARN>|
|AZ_1|<AvailabilityZones>|
|AZ_2|<AvailabilityZones>|
|SUBNET|<SubnetのID>|
|MAX_SIZE|<EC2の最低起動台数>|
|MIN_SIZE|<EC2の最高起動台数>|

- Blue/Green Deploy用

|Key|Value|
|:--|:--|
|SSM_NEW_ASG|new_asg|
|SSM_OLD_ASG|old_asg|
|ALB_TARGET|<ALBのARN>|

# 参考
https://github.com/awslabs/ami-builder-packer
