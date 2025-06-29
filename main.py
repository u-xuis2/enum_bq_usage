#!/usr/bin/env python3
"""
BigQuery Usage Monitoring Tool
データストレージとクエリ処理量の使用状況を監視するシステム
"""

import json
import sys
import traceback
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account


@dataclass
class DatasetUsage:
    """データセット使用量情報"""
    dataset_id: str
    size_bytes: int
    size_gb: float
    size_tb: float
    cost_usd: float
    cost_jpy: float


@dataclass
class UserQueryUsage:
    """ユーザー別クエリ使用量"""
    user_email: str
    bytes_processed: int
    tb_processed: float
    cost_usd: float
    cost_jpy: float


class ConfigurationManager:
    """設定管理クラス"""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"設定ファイルが見つかりません: {config_path}")
            
            with config_file.open("r", encoding="utf-8") as file:
                config_data = json.load(file)
            
            ConfigurationManager._validate_config(config_data)
            return config_data
            
        except Exception as error:
            print(f"設定読み込みでエラーが発生: {error}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            sys.exit(101)
    
    @staticmethod
    def _validate_config(config: Dict[str, Any]) -> None:
        """設定内容の検証"""
        essential_fields = ["project_id", "region", "key_file", "datasets"]
        missing_fields = [field for field in essential_fields if field not in config]
        
        if missing_fields:
            raise ValueError(f"必須設定項目が不足: {', '.join(missing_fields)}")


class BigQueryClientFactory:
    """BigQueryクライアント生成クラス"""
    
    @staticmethod
    def create_client(key_file_path: str, project_id: str) -> bigquery.Client:
        """認証情報を使用してBigQueryクライアントを生成"""
        try:
            credentials = service_account.Credentials.from_service_account_file(key_file_path)
            return bigquery.Client(credentials=credentials, project=project_id)
        except Exception as error:
            print(f"BigQueryクライアント作成時エラー: {error}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            sys.exit(102)


class StorageAnalyzer:
    """ストレージ使用量分析クラス"""
    
    # 料金設定
    STORAGE_RATE_USD_PER_GB = 0.02  # 月額
    USD_TO_JPY_RATE = 150
    
    def __init__(self, client: bigquery.Client, project_id: str):
        self.client = client
        self.project_id = project_id
    
    def analyze_datasets(self, dataset_list: List[str]) -> Dict[str, Any]:
        """データセット群のストレージ使用量を分析"""
        try:
            dataset_usages = []
            total_storage_bytes = 0
            
            for dataset_name in dataset_list:
                usage = self._analyze_single_dataset(dataset_name)
                dataset_usages.append(usage)
                total_storage_bytes += usage.size_bytes
            
            return self._compile_storage_summary(dataset_usages, total_storage_bytes)
            
        except Exception as error:
            print(f"ストレージ分析でエラーが発生: {error}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            sys.exit(103)
    
    def _analyze_single_dataset(self, dataset_name: str) -> DatasetUsage:
        """単一データセットの使用量分析"""
        try:
            dataset_ref = self.client.dataset(dataset_name, project=self.project_id)
            dataset_obj = self.client.get_dataset(dataset_ref)
            tables = list(self.client.list_tables(dataset_ref))
            
            dataset_total_bytes = 0
            for table in tables:
                table_obj = self.client.get_table(table.reference)
                if hasattr(table_obj, "num_bytes") and table_obj.num_bytes is not None:
                    dataset_total_bytes += table_obj.num_bytes
            
            return self._calculate_dataset_costs(dataset_name, dataset_total_bytes)
            
        except Exception as error:
            print(f"データセット {dataset_name} 分析エラー: {error}", file=sys.stderr, flush=True)
            return DatasetUsage(
                dataset_id=dataset_name,
                size_bytes=0,
                size_gb=0.0,
                size_tb=0.0,
                cost_usd=0.0,
                cost_jpy=0.0
            )
    
    def _calculate_dataset_costs(self, dataset_name: str, bytes_count: int) -> DatasetUsage:
        """データセットのコスト計算"""
        gb_size = bytes_count / (1024 ** 3)
        tb_size = gb_size / 1024
        monthly_cost_usd = gb_size * self.STORAGE_RATE_USD_PER_GB
        monthly_cost_jpy = monthly_cost_usd * self.USD_TO_JPY_RATE
        
        return DatasetUsage(
            dataset_id=dataset_name,
            size_bytes=bytes_count,
            size_gb=round(gb_size, 3),
            size_tb=round(tb_size, 6),
            cost_usd=round(monthly_cost_usd, 2),
            cost_jpy=round(monthly_cost_jpy, 2)
        )
    
    def _compile_storage_summary(self, usages: List[DatasetUsage], total_bytes: int) -> Dict[str, Any]:
        """ストレージ使用量サマリーの作成"""
        total_gb = total_bytes / (1024 ** 3)
        total_monthly_cost_usd = total_gb * self.STORAGE_RATE_USD_PER_GB
        total_monthly_cost_jpy = total_monthly_cost_usd * self.USD_TO_JPY_RATE
        
        return {
            "datasets": [
                {
                    "dataset_id": usage.dataset_id,
                    "size_bytes": usage.size_bytes,
                    "size_gb": usage.size_gb,
                    "size_tb": usage.size_tb,
                    "cost_usd": usage.cost_usd,
                    "cost_jpy": usage.cost_jpy,
                }
                for usage in usages
            ],
            "total_size_bytes": total_bytes,
            "total_cost_usd": round(total_monthly_cost_usd, 2),
            "total_cost_jpy": round(total_monthly_cost_jpy, 2),
        }


class QueryAnalyzer:
    """クエリ使用量分析クラス"""
    
    # 料金設定
    QUERY_RATE_USD_PER_TB = 6.0
    USD_TO_JPY_RATE = 150
    
    def __init__(self, client: bigquery.Client, project_id: str, region: str):
        self.client = client
        self.project_id = project_id
        self.region = region
    
    def analyze_recent_queries(self) -> Dict[str, Any]:
        """直近24時間のクエリ使用量を分析（ユーザー別）"""
        try:
            time_range = self._get_time_range()
            query_statement = self._build_usage_query(time_range)
            
            job_config = bigquery.QueryJobConfig()
            query_job = self.client.query(query_statement, job_config=job_config)
            results = list(query_job.result())
            
            return self._process_query_results(results)
            
        except Exception as error:
            print(f"クエリ分析でエラーが発生: {error}", file=sys.stderr, flush=True)
            print(traceback.format_exc(), file=sys.stderr, flush=True)
            # エラー時は空の結果を返す
            return {
                "users": [],
                "total_bytes_processed": 0,
                "total_tb_processed": 0,
                "total_cost_usd": 0,
                "total_cost_jpy": 0,
            }
    
    def _get_time_range(self) -> tuple:
        """分析対象の時間範囲を取得"""
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(days=1)
        return start_time, current_time
    
    def _build_usage_query(self, time_range: tuple) -> str:
        """使用量取得用のSQLクエリを構築"""
        start_time, end_time = time_range
        
        return f"""
        SELECT
            user_email,
            SUM(total_bytes_processed) as total_bytes_processed
        FROM
            `{self.project_id}.region-{self.region}.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE
            creation_time >= TIMESTAMP('{start_time.isoformat()}')
            AND creation_time <= TIMESTAMP('{end_time.isoformat()}')
            AND job_type = 'QUERY'
            AND state = 'DONE'
            AND total_bytes_processed IS NOT NULL
            AND user_email IS NOT NULL
        GROUP BY user_email
        ORDER BY total_bytes_processed DESC
        """
    
    def _process_query_results(self, results) -> Dict[str, Any]:
        """クエリ結果の処理と集計"""
        user_usages = []
        grand_total_bytes = 0
        
        for row in results:
            processed_bytes = row.total_bytes_processed or 0
            grand_total_bytes += processed_bytes
            
            user_usage = self._calculate_user_costs(row.user_email, processed_bytes)
            user_usages.append(user_usage)
        
        return self._compile_query_summary(user_usages, grand_total_bytes)
    
    def _calculate_user_costs(self, email: str, bytes_processed: int) -> UserQueryUsage:
        """ユーザー別のクエリコスト計算"""
        tb_processed = bytes_processed / (1024 ** 4)
        cost_usd = tb_processed * self.QUERY_RATE_USD_PER_TB
        cost_jpy = cost_usd * self.USD_TO_JPY_RATE
        
        return UserQueryUsage(
            user_email=email,
            bytes_processed=bytes_processed,
            tb_processed=round(tb_processed, 6),
            cost_usd=round(cost_usd, 2),
            cost_jpy=round(cost_jpy, 2)
        )
    
    def _compile_query_summary(self, usages: List[UserQueryUsage], total_bytes: int) -> Dict[str, Any]:
        """クエリ使用量サマリーの作成"""
        total_tb = total_bytes / (1024 ** 4)
        total_cost_usd = total_tb * self.QUERY_RATE_USD_PER_TB
        total_cost_jpy = total_cost_usd * self.USD_TO_JPY_RATE
        
        return {
            "users": [
                {
                    "user_email": usage.user_email,
                    "bytes_processed": usage.bytes_processed,
                    "tb_processed": usage.tb_processed,
                    "cost_usd": usage.cost_usd,
                    "cost_jpy": usage.cost_jpy,
                }
                for usage in usages
            ],
            "total_bytes_processed": total_bytes,
            "total_tb_processed": round(total_tb, 6),
            "total_cost_usd": round(total_cost_usd, 2),
            "total_cost_jpy": round(total_cost_jpy, 2),
        }


class UsageReporter:
    """使用量レポート生成クラス"""
    
    @staticmethod
    def generate_report(storage_analysis: Dict[str, Any], query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """統合レポートの生成"""
        return {
            "storage": storage_analysis,
            "query": query_analysis
        }
    
    @staticmethod
    def output_report(report_data: Dict[str, Any]) -> None:
        """レポートの標準出力への出力"""
        json_output = json.dumps(report_data, ensure_ascii=False, indent=2)
        print(json_output, flush=True)


def execute_monitoring():
    """メイン実行フロー"""
    # 設定の読み込み
    config = ConfigurationManager.load_config("settings.json")
    
    # BigQueryクライアントの初期化
    bq_client = BigQueryClientFactory.create_client(
        config["key_file"], 
        config["project_id"]
    )
    
    # ストレージ使用量の分析
    storage_analyzer = StorageAnalyzer(bq_client, config["project_id"])
    storage_results = storage_analyzer.analyze_datasets(config["datasets"])
    
    # クエリ使用量の分析
    query_analyzer = QueryAnalyzer(bq_client, config["project_id"], config["region"])
    query_results = query_analyzer.analyze_recent_queries()
    
    # レポート生成と出力
    final_report = UsageReporter.generate_report(storage_results, query_results)
    UsageReporter.output_report(final_report)


if __name__ == "__main__":
    execute_monitoring()