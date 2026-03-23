"""
S3 File Reader - Reads files from AWS S3 buckets
"""

import logging
import io
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Optional imports
try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False
    logger.warning("boto3 not available - S3 support disabled")


class S3FileReader:
    """Reads files from AWS S3 buckets and provides them as local file paths."""

    def __init__(self, region_name: str = None, aws_access_key_id: str = None,
                 aws_secret_access_key: str = None, aws_session_token: str = None):
        """
        Initialize S3 client.

        Args:
            region_name: AWS region (can also be set via AWS_DEFAULT_REGION env var)
            aws_access_key_id: AWS access key (can also be set via AWS_ACCESS_KEY_ID env var)
            aws_secret_access_key: AWS secret key (can also be set via AWS_SECRET_ACCESS_KEY env var)
            aws_session_token: AWS session token for temporary credentials
        """
        if not HAS_BOTO3:
            raise ImportError("boto3 not available for S3 operations")

        self.s3_client = boto3.client(
            's3',
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token
        )

    def download_to_temp_file(self, s3_url: str) -> str:
        """
        Download file from S3 to a temporary local file.

        Args:
            s3_url: S3 URL in format s3://bucket-name/key-name

        Returns:
            Local file path to the downloaded file

        Raises:
            ValueError: If URL format is invalid
            ClientError: If S3 operation fails
        """
        bucket_name, key_name = self._parse_s3_url(s3_url)

        try:
            # Get object metadata first to determine filename
            response = self.s3_client.head_object(Bucket=bucket_name, Key=key_name)
            content_type = response.get('ContentType', 'application/octet-stream')

            # Determine file extension from content type or key name
            file_extension = self._get_extension_from_content_type(content_type, key_name)

            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_path = temp_file.name

            # Download the file
            self.s3_client.download_file(bucket_name, key_name, temp_path)

            logger.info(f"Downloaded s3://{bucket_name}/{key_name} to {temp_path}")
            return temp_path

        except NoCredentialsError:
            raise ClientError(
                error_response={"Error": {"Code": "NoCredentialsError", "Message": "AWS credentials not found"}},
                operation_name="DownloadFile"
            )
        except ClientError as e:
            logger.error(f"S3 download failed for {s3_url}: {e}")
            raise

    def read_file_content(self, s3_url: str) -> bytes:
        """
        Read file content directly from S3 as bytes.

        Args:
            s3_url: S3 URL in format s3://bucket-name/key-name

        Returns:
            File content as bytes
        """
        bucket_name, key_name = self._parse_s3_url(s3_url)

        try:
            response = self.s3_client.get_object(Bucket=bucket_name, Key=key_name)
            return response['Body'].read()
        except ClientError as e:
            logger.error(f"S3 read failed for {s3_url}: {e}")
            raise

    def get_file_info(self, s3_url: str) -> Dict[str, Any]:
        """
        Get file metadata from S3.

        Args:
            s3_url: S3 URL in format s3://bucket-name/key-name

        Returns:
            Dict with file metadata
        """
        bucket_name, key_name = self._parse_s3_url(s3_url)

        try:
            response = self.s3_client.head_object(Bucket=bucket_name, Key=key_name)

            return {
                'bucket': bucket_name,
                'key': key_name,
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'etag': response.get('ETag'),
                'storage_class': response.get('StorageClass', 'STANDARD'),
                'url': s3_url
            }
        except ClientError as e:
            logger.error(f"S3 head_object failed for {s3_url}: {e}")
            raise

    def _parse_s3_url(self, s3_url: str) -> tuple[str, str]:
        """
        Parse S3 URL into bucket and key.

        Args:
            s3_url: URL in format s3://bucket-name/key-name

        Returns:
            Tuple of (bucket_name, key_name)
        """
        if not s3_url.startswith('s3://'):
            raise ValueError(f"Invalid S3 URL format: {s3_url}. Expected s3://bucket/key")

        parsed = urlparse(s3_url)
        bucket_name = parsed.netloc
        key_name = parsed.path.lstrip('/')

        if not bucket_name or not key_name:
            raise ValueError(f"Invalid S3 URL: {s3_url}. Missing bucket or key")

        return bucket_name, key_name

    def _get_extension_from_content_type(self, content_type: str, key_name: str) -> str:
        """Determine file extension from content type or key name."""
        # Common content type to extension mapping
        content_type_extensions = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'text/csv': '.csv',
            'text/plain': '.txt',
            'application/json': '.json',
            'text/markdown': '.md',
            'application/yaml': '.yaml'
        }

        # Try content type first
        if content_type in content_type_extensions:
            return content_type_extensions[content_type]

        # Fall back to key name extension
        key_path = Path(key_name)
        if key_path.suffix:
            return key_path.suffix

        # Default to .bin for unknown types
        return '.bin'

    def is_s3_url(self, url: str) -> bool:
        """Check if URL is an S3 URL."""
        return url.startswith('s3://')

    def list_bucket_files(self, bucket_name: str, prefix: str = "", max_keys: int = 100) -> List[Dict[str, Any]]:
        """
        List files in an S3 bucket with optional prefix.

        Args:
            bucket_name: S3 bucket name
            prefix: Key prefix to filter files
            max_keys: Maximum number of files to return

        Returns:
            List of file info dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'url': f"s3://{bucket_name}/{obj['Key']}"
                    })

            return files
        except ClientError as e:
            logger.error(f"S3 list_objects failed for bucket {bucket_name}: {e}")
            raise