# 実装上の注意点

* 関数名はスネークケース
* シェルは実行権限を信用せずかならずbash <シェル名>で実行する
* shファイル作成時は次の初期化処理であること

```
umask 077
set -uo pipefail

RUN_PATH=`pwd`
EXE_PATH=`dirname "${0}"`
EXE_NAME=`basename "${0}"`
cd "${EXE_PATH}"
EXE_PATH=`pwd`

```

## その他の注意事項

* コメントは日本語で記載
* 関数コメントは引数の説明は不要
* パフォーマンスも考慮
* セキュリティチェックは厳し目に実装
* テスト時はカバレッジを重視
* 処理の都合上長時間のsleepをする場合はsleepは一秒程度としてそのループを回して実行状態のチェックは定期的に実施するような処理とすること

## pythonを実装時の追加事項(他の言語対象外)

* Exception処理時にはスタックトレースも表示
* Exception as eを文字列化する場合はstrではなくreprを使用する
* exitの戻り値は判別がつくように100からインクリメントする
* json文字列にするときはensure_ascii=Falseを必須
* printするときもflash=Trueを指定
* エラー処理デバッグ処理はstderrに出力すること、stdoutは正常系のデータ出力に使用する。
* unicornを使う場合はコマンドでの起動にしてください。
* 例:uvicorn main:app --host 127.0.0.1 --port 8000 --reload --reload-dir . --reload-exclude logs

## node+reactの実装時の追加事項

* 外部からのアクセスする際のURLはsettings.jsonにbaseURLで設定します。これは基本的にはリバースプロキシでアクセスするので、そのbaseURL基準でHTTPもHTTPSもドメインもポートもクライアントからのアクセス時には全部切り替わるようにしてください。
* HTTPS前提でヘッダは調整する。
* viteを利用する。

## その他

コミットメッセージにclaudeなどの情報は不要です。
具体的には以下のような記述です。

```
Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>
```

## supervisorの設定

supervisorの設定の手順は定型化したいため、以下の手順を参考にしてください。
シェルの中身自体は必要に応じた調整してもよいです。

### confファイルの雛形

以下を参考にしてください。
特に、次のグループでの停止が重要です。
killasgroup=true
stopasgroup=true

```
[program:__PORJECT_NAME__]
command=__PROJECT_PATH__/start.sh
directory=__PROJECT_PATH__
user=__USER__
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=__PROJECT_PATH__/logs/__PORJECT_NAME__.log
stdout_logfile_maxbytes=10MB
stdout_logfile_backups=30
startretries=3
startsecs=0
stopsignal=TERM
stopwaitsecs=30
killasgroup=true
stopasgroup=true
environment=PATH="__PATH__"
```

また以下のような設定のsetupシェルを用意してください。
__PROJECT_PATH__や__PATH__はフルパスで記載してください。

### setup_supervisor.sh

```
#!/bin/bash

PROJECT_NAME=my_project_name
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_PATH="$(dirname "$SCRIPT_DIR")"
USER=$(whoami)
PATH_ENV="$PATH"

echo "プロジェクトパス: $PROJECT_PATH"
echo "実行ユーザー: $USER"

mkdir -p "$PROJECT_PATH/logs"

sed "s|__PROJECT_PATH__|$PROJECT_PATH|g; s|__USER__|$USER|g; s|__PATH__|$PATH_ENV|g" \
    "$SCRIPT_DIR/$PROJECT_NAME.conf.template" > "$SCRIPT_DIR/$PROJECT_NAME.conf"

echo "supervisor設定ファイルを生成しました: $SCRIPT_DIR/$PROJECT_NAME.conf"
echo ""
echo "次の手順でsupervisorに登録してください:"
echo "1. sudo cp $SCRIPT_DIR/$PROJECT_NAME.conf /etc/supervisor/conf.d/"
echo "2. sudo supervisorctl reread"
echo "3. sudo supervisorctl update"
echo "4. sudo supervisorctl start $PROJECT_NAME"
```
