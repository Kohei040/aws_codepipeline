- 実行の流れ
  1．Git push
  2．Code Pipelineで検知
  3．Code Build(1)を実行
      - DokcerにPackerをインストール&実行
      - PackerのイメージからEC2作成
      - 作成したEC2でAnsible実行
      - AMIを作成
  4．Code Build(2)を実行
      - テスト？
  5．Code DeployもしくはCode Buildでカスタムデプロイ

参考：
https://github.com/awslabs/ami-builder-packer
