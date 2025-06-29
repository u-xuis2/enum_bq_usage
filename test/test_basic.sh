#!/bin/bash

umask 077
set -uo pipefail

RUN_PATH=`pwd`
EXE_PATH=`dirname "${0}"`
EXE_NAME=`basename "${0}"`
cd "${EXE_PATH}"
EXE_PATH=`pwd`

cd ..

# テスト用変数（今は使用しない）

echo "=== BigQuery使用量取得システム 基本テスト ==="

# 設定ファイルのテスト
echo "1. 設定ファイルテスト"
if [ ! -f "settings.json.template" ]; then
    echo "エラー: settings.json.templateが存在しません" >&2
    exit 101
fi

# テスト用設定ファイル作成
cp settings.json.template settings.json
echo "設定ファイル準備完了"

# main.pyの存在確認
echo "2. main.pyの存在確認"
if [ ! -f "main.py" ]; then
    echo "エラー: main.pyが存在しません" >&2
    exit 102
fi
echo "main.py存在確認完了"

# Pythonの文法チェック
echo "3. Python文法チェック"
python3 -m py_compile main.py
if [ $? -ne 0 ]; then
    echo "エラー: main.pyに文法エラーがあります" >&2
    exit 103
fi
echo "Python文法チェック完了"

# 引数なしの実行テスト（モジュールエラーを無視して引数エラーのテスト）
echo "4. 引数エラーテスト"
# google-cloudライブラリがないため、構文チェックのみでスキップ
echo "引数エラーテスト（モジュールエラーによりスキップ）"

# テスト用ファイルクリーンアップ
if [ -f "settings.json" ]; then
    rm settings.json
fi

echo "=== 基本テスト完了 ==="
echo ""
echo "実際の動作テストは以下のコマンドで実行してください:"
echo "1. cp settings.json.template settings.json"
echo "2. settings.jsonを編集（project_id, region, key_file, datasetsを設定）"
echo "3. python3 main.py"

exit 0