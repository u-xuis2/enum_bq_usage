#!/bin/bash

umask 077
set -uo pipefail

RUN_PATH=`pwd`
EXE_PATH=`dirname "${0}"`
EXE_NAME=`basename "${0}"`
cd "${EXE_PATH}"
EXE_PATH=`pwd`

echo "=== BigQuery使用量取得システム 環境構築 ==="

# Pythonバージョン確認
echo "1. Pythonバージョン確認"
python3 --version
if [ $? -ne 0 ]; then
    echo "エラー: Python3がインストールされていません" >&2
    exit 101
fi

# pipバージョン確認
echo "2. pipバージョン確認"
pip3 --version
if [ $? -ne 0 ]; then
    echo "エラー: pip3がインストールされていません" >&2
    exit 102
fi

# 必要なライブラリをインストール
echo "3. 必要なライブラリのインストール"
pip3 install google-cloud-bigquery>=3.0.0 google-auth>=2.0.0
if [ $? -ne 0 ]; then
    echo "エラー: ライブラリのインストールに失敗しました" >&2
    exit 103
fi

# 設定ファイルの準備
echo "4. 設定ファイルの準備"
if [ ! -f "settings.json" ]; then
    if [ -f "settings.json.template" ]; then
        cp settings.json.template settings.json
        echo "settings.jsonを作成しました"
        echo "必要に応じて設定を編集してください"
    else
        echo "エラー: settings.json.templateが見つかりません" >&2
        exit 104
    fi
else
    echo "settings.jsonは既に存在します"
fi

# ディレクトリ作成
echo "5. ディレクトリ作成"
mkdir -p logs
if [ $? -eq 0 ]; then
    echo "logsディレクトリを作成しました"
fi

echo "=== 環境構築完了 ==="
echo ""
echo "使用方法:"
echo "1. settings.jsonを編集して必要な設定を行う"
echo "   - project_id: BigQueryプロジェクトID"
echo "   - region: 対象リージョン"
echo "   - key_file: サービスアカウントJSONキーファイルパス"
echo "   - datasets: 対象データセット名のリスト"
echo "2. 以下のコマンドで実行:"
echo "   python3 main.py"
echo ""
echo "テスト実行:"
echo "   bash test/test_basic.sh"

exit 0