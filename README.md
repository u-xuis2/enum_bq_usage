# BigQuery使用量取得システム

BigQueryのストレージ使用量とクエリ利用量を取得し、JSON形式で出力するシンプルなシステムです。

## インストール

### 必要な環境
- Python 3.8以上
- pip
- BigQuery API有効化済みのGCPプロジェクト

### セットアップ

1. 環境構築スクリプトを実行
```bash
bash ready.sh
```

2. 設定ファイルを編集
```bash
cp settings.json.template settings.json
```

`settings.json`で必要な情報を設定:
```json
{
  "project_id": "your-project-id",
  "region": "us-central1", 
  "key_file": "path/to/your-service-account-key.json",
  "datasets": [
    "your_dataset1",
    "your_dataset2"
  ]
}
```

3. BigQueryサービスアカウントJSONキーファイルを準備

## 使用方法

```bash
python3 main.py
```

設定ファイル（settings.json）から自動的に設定を読み取って実行します。

### 実行例
```bash
python3 main.py
```

## 出力形式

JSON形式で使用量とコスト情報を出力:
```json
{
  "storage": {
    "datasets": [
      {
        "dataset_id": "dataset1",
        "size_bytes": 1073741824,
        "size_gb": 1.0,
        "size_tb": 0.001,
        "cost_usd": 0.02,
        "cost_jpy": 3.0
      }
    ],
    "total_size_bytes": 1073741824,
    "total_cost_usd": 0.02,
    "total_cost_jpy": 3.0
  },
  "query": {
    "users": [
      {
        "user_email": "user1@example.com",
        "bytes_processed": 536870912,
        "tb_processed": 0.0005,
        "cost_usd": 3.0,
        "cost_jpy": 450.0
      },
      {
        "user_email": "user2@example.com",
        "bytes_processed": 536870912,
        "tb_processed": 0.0005,
        "cost_usd": 3.0,
        "cost_jpy": 450.0
      }
    ],
    "total_bytes_processed": 1073741824,
    "total_tb_processed": 0.001,
    "total_cost_usd": 6.0,
    "total_cost_jpy": 900.0
  }
}
```

## テスト

基本動作テストを実行:
```bash
bash test/test_basic.sh
```

## 機能

- ストレージ使用量取得（データセット別）
- クエリ使用量取得（24時間以内、メールアドレス別集計）
- USD/JPY換算（150円固定）
- JSON形式での結果出力

### クエリ使用量の詳細
- 各ユーザーのメールアドレス別にクエリ処理量を集計
- 使用量の多い順でソート
- ユーザー別とプロジェクト全体の両方でコスト計算