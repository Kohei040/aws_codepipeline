【AWS】AutoScaling環境でのCI/CD
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

# Lambdaの環境について
- Python3.6
- IAM Roleは下記参照

# Lambdaの環境変数
各Lambdaで設定する環境は以下となる

- LaunchConfig作成用

|Key|Value|
|:--|:--|
|SSM_AMI|ami_id|
|SSM_LC|lc_name|
|INSTANCE_TYPE|t3.micro|
|SG_ID|sg-xxxxxx|
|IAM_ROLE|'作成したRole'|
|PRE_LC_NAME|'LCのPrefix'|

- AutoScalingGroup作成用

|Key|Value|
|:--|:--|
|SSM_NEW_ASG|new_asg|
|SSM_OLD_ASG|old_asg|
|ASG_NAME|'ASGのPrefix'|
|SSM_LC|lc_name|
|ALB_TARGET|'ALBのARN'|
|AZ_1|'AvailabilityZones'|
|AZ_2|'AvailabilityZones'|
|SUBNET|'SubnetのID'|
|MAX_SIZE|'EC2の最低起動台数'|
|MIN_SIZE|'EC2の最高起動台数|

- Blue/Green Deploy用

|Key|Value|
|:--|:--|
|SSM_NEW_ASG|new_asg|
|SSM_OLD_ASG|old_asg|
|ALB_TARGET|'ALBのARN'|

# System Manager Parameter
AWS System ManagerのParameter Storeの用途は、
CodePipeline上で作成した成果物を引き継ぐために利用する

|Name|Type|Value|
|:--|:--|:--|
|ami_id|String|ami-xxxxxxxx|
|lc_name|String|'LaunchConfigのName'|
|new_asg|String|'新AutoScalingGroupのName'|
|old_asg|String|'新AutoScalingGroupのName'|

# IAM Role
各サービスにアタッチするIAM Roleのポリシーは以下となる

- Lambda(共通) 
  - AWSLambdaExecute(AWS managed policy)
  - AWSCodePipelineFullAccess(AWS managed policy)
  - AmazonEC2FullAccess(AWS managed policy)
  - AmazonSSMFullAccess(AWS managed policy)
  - IAMFullAccess(AWS managed policy)

- CodePipeline
  - CodePipeline実行用(Managed policy)
    - CodePipeline作成時に自動生成されます

- CodeBuild
  - AmazonSSMFullAccess(AWS managed policy)
  - CodeBuild実行用(Managed policy)
    - CodeBuild作成時に自動生成されます
  - Packer実行用(Managed policy)
```
{
  "Version": "2012-10-17",
  "Statement": [{
      "Effect": "Allow",
      "Action" : [
        "ec2:AttachVolume",
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:CopyImage",
        "ec2:CreateImage",
        "ec2:CreateKeypair",
        "ec2:CreateSecurityGroup",
        "ec2:CreateSnapshot",
        "ec2:CreateTags",
        "ec2:CreateVolume",
        "ec2:DeleteKeyPair",
        "ec2:DeleteSecurityGroup",
        "ec2:DeleteSnapshot",
        "ec2:DeleteVolume",
        "ec2:DeregisterImage",
        "ec2:DescribeImageAttribute",
        "ec2:DescribeImages",
        "ec2:DescribeInstances",
        "ec2:DescribeRegions",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSnapshots",
        "ec2:DescribeSubnets",
        "ec2:DescribeTags",
        "ec2:DescribeVolumes",
        "ec2:DetachVolume",
        "ec2:GetPasswordData",
        "ec2:ModifyImageAttribute",
        "ec2:ModifyInstanceAttribute",
        "ec2:ModifySnapshotAttribute",
        "ec2:RegisterImage",
        "ec2:RunInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances"
      ],
      "Resource" : "*"
  }]
}
```

# 参考
https://github.com/awslabs/ami-builder-packer
