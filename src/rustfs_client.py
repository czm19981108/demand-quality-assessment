"""RustFS 对象存储客户端

兼容 S3 API，使用 boto3 进行操作
"""
import os
from typing import Optional, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from loguru import logger

from .config import config


class RustFSClient:
    """RustFS 对象存储客户端，兼容 S3 API"""

    _instance: Optional['RustFSClient'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._client = None
        self._enabled = config.rustfs_enabled
        self._endpoint = config.rustfs_endpoint
        self._access_key = config.rustfs_access_key
        self._secret_key = config.rustfs_secret_key
        self._bucket = config.rustfs_bucket
        self._region = config.rustfs_region

        if self._enabled:
            self._init_client()

    def _init_client(self):
        """初始化 S3 客户端"""
        if not self._access_key or not self._secret_key:
            logger.warning("RustFS: AccessKey or SecretKey 未配置，禁用 RustFS")
            self._enabled = False
            return

        try:
            self._client = boto3.client(
                's3',
                endpoint_url=self._endpoint,
                aws_access_key_id=self._access_key,
                aws_secret_access_key=self._secret_key,
                region_name=self._region
            )
            logger.info(f"RustFS 客户端初始化成功: endpoint={self._endpoint}, bucket={self._bucket}")
        except Exception as e:
            logger.error(f"RustFS 客户端初始化失败: {e}")
            self._enabled = False
            self._client = None

    @property
    def enabled(self) -> bool:
        """是否启用 RustFS"""
        return self._enabled and self._client is not None

    def ensure_bucket_exists(self) -> bool:
        """确保 Bucket 存在，如果不存在则创建"""
        if not self.enabled:
            return False

        try:
            self._client.head_bucket(Bucket=self._bucket)
            logger.debug(f"RustFS: Bucket {self._bucket} 已存在")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket 不存在，创建它
                try:
                    self._client.create_bucket(Bucket=self._bucket)
                    logger.info(f"RustFS: 创建 Bucket {self._bucket} 成功")
                    return True
                except Exception as create_e:
                    logger.error(f"RustFS: 创建 Bucket {self._bucket} 失败: {create_e}")
                    return False
            else:
                logger.error(f"RustFS: 检查 Bucket 失败: {e}")
                return False

    def upload_report(self, requirement_id: str, report_content: str) -> Tuple[bool, str]:
        """上传评估报告到 RustFS

        Args:
            requirement_id: 需求ID
            report_content: Markdown 报告内容

        Returns:
            (success, object_key): 是否成功，以及对象键
        """
        if not self.enabled:
            return False, ""

        if not self.ensure_bucket_exists():
            return False, ""

        # 生成对象键：需求ID_时间戳.md
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        object_key = f"{requirement_id}_{timestamp}.md"

        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=object_key,
                Body=report_content.encode('utf-8'),
                ContentType='text/markdown; charset=utf-8'
            )
            logger.info(f"RustFS: 报告上传成功: {object_key}")
            return True, object_key
        except Exception as e:
            logger.error(f"RustFS: 报告上传失败: {e}")
            return False, ""

    def download_report(self, object_key: str) -> Tuple[bool, Optional[str]]:
        """从 RustFS 下载报告

        Args:
            object_key: 对象键

        Returns:
            (success, content): 是否成功，以及报告内容
        """
        if not self.enabled:
            return False, None

        try:
            response = self._client.get_object(Bucket=self._bucket, Key=object_key)
            content = response['Body'].read().decode('utf-8')
            logger.debug(f"RustFS: 报告下载成功: {object_key}")
            return True, content
        except Exception as e:
            logger.error(f"RustFS: 报告下载失败: {e}")
            return False, None

    def delete_report(self, object_key: str) -> bool:
        """删除报告

        Args:
            object_key: 对象键

        Returns:
            是否删除成功
        """
        if not self.enabled:
            return False

        try:
            self._client.delete_object(Bucket=self._bucket, Key=object_key)
            logger.info(f"RustFS: 报告删除成功: {object_key}")
            return True
        except Exception as e:
            logger.error(f"RustFS: 报告删除失败: {e}")
            return False

    def get_report_url(self, object_key: str) -> str:
        """获取报告的访问 URL

        Args:
            object_key: 对象键

        Returns:
            访问 URL
        """
        if not self.enabled:
            return ""

        return f"{self._endpoint}/{self._bucket}/{object_key}"

    def list_reports(self, prefix: str = "") -> list:
        """列出所有报告

        Args:
            prefix: 前缀过滤

        Returns:
            对象列表
        """
        if not self.enabled:
            return []

        try:
            if prefix:
                response = self._client.list_objects_v2(Bucket=self._bucket, Prefix=prefix)
            else:
                response = self._client.list_objects_v2(Bucket=self._bucket)

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]
        except Exception as e:
            logger.error(f"RustFS: 列出对象失败: {e}")
            return []


# 全局客户端实例
rustfs_client = RustFSClient()


def get_rustfs_client() -> RustFSClient:
    """获取全局 RustFS 客户端实例"""
    return rustfs_client
