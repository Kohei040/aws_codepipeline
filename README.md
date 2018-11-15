【AWS】AutoSCaling環境でのCI/CD
==============================

# CI/CDの流れ

![CI/Cd](https://github.com/Kohei040/aws_code_series_validation/raw/test/image/CICD_Flow.PNG)

1. githubへpush
1. CodePipelineで検知
1. [CodeBuild]AMI作成
1. [Lambda]LaunchConfig作成
1. [Lambda]AutoScalingGroup作成
1. [Lambda]Blue/Green deploymnet実施

※2の手順以降は全てCodePipeline上で管理

# Golden AMI作成方式

![Create_GoledenAMI](https://github.com/Kohei040/aws_code_series_validation/raw/test/image/Create_Golden_AMI.PNG)

1. CodeBuildの処理をするDockerコンテナを起動
1. DockerコンテナにPacker&Ansibleインストール
1. DockerコンテナがPackerの処理を実行
1. Packerが指定したEC2を起動、Ansibleの処理実行
1. EC2のAMIを取得、EC2削除

# 参考
https://github.com/awslabs/ami-builder-packer
