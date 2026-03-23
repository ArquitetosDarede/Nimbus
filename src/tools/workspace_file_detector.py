"""
Workspace File Detector - Automatically detects relevant files in the current workspace
"""

import logging
import os
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class WorkspaceFileDetector:
    """Detects and analyzes files in the current workspace directory."""

    # Supported file extensions for analysis
    SUPPORTED_EXTENSIONS = {
        '.pdf', '.docx', '.xlsx', '.xls', '.csv', '.txt',
        '.md', '.json', '.yaml', '.yml'  # Additional text-based formats
    }

    # File patterns to ignore
    IGNORE_PATTERNS = {
        'node_modules', '.git', '__pycache__', '.vscode', '.idea',
        'build', 'dist', '.next', '.nuxt', 'target', 'bin', 'obj',
        '.DS_Store', 'Thumbs.db', '*.log', '*.tmp', '*.bak'
    }

    def __init__(self, workspace_root: str = None):
        """
        Initialize with workspace root directory.

        Args:
            workspace_root: Root directory to scan. If None, uses current working directory.
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()

    def detect_relevant_files(self, max_depth: int = 3, include_hidden: bool = False) -> List[Dict[str, Any]]:
        """
        Scan workspace and return list of relevant files for analysis.

        Args:
            max_depth: Maximum directory depth to scan
            include_hidden: Whether to include hidden files/directories

        Returns:
            List of file info dictionaries with metadata
        """
        relevant_files = []

        try:
            for root, dirs, files in os.walk(self.workspace_root, topdown=True):
                # Skip ignored directories
                dirs[:] = [d for d in dirs if self._should_include_dir(d, include_hidden)]

                current_depth = len(Path(root).relative_to(self.workspace_root).parts)
                if current_depth > max_depth:
                    continue

                for file in files:
                    file_path = Path(root) / file

                    if self._is_relevant_file(file_path):
                        file_info = self._analyze_file_metadata(file_path)
                        relevant_files.append(file_info)

        except Exception as e:
            logger.error(f"Error scanning workspace: {e}")

        # Sort by relevance (recently modified first, then by size)
        relevant_files.sort(key=lambda x: (x['modified_time'], x['size']), reverse=True)

        return relevant_files

    def _should_include_dir(self, dirname: str, include_hidden: bool) -> bool:
        """Check if directory should be included in scan."""
        if dirname in self.IGNORE_PATTERNS:
            return False
        if not include_hidden and dirname.startswith('.'):
            return False
        return True

    def _is_relevant_file(self, file_path: Path) -> bool:
        """Check if file is relevant for analysis."""
        if not file_path.exists() or not file_path.is_file():
            return False

        # Check extension
        if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        # Skip very small files (likely not useful)
        if file_path.stat().st_size < 100:  # Less than 100 bytes
            return False

        # Skip very large files (likely binaries or logs)
        if file_path.stat().st_size > 50 * 1024 * 1024:  # More than 50MB
            return False

        return True

    def _analyze_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Analyze file metadata for relevance scoring."""
        stat = file_path.stat()

        return {
            'path': str(file_path),
            'name': file_path.name,
            'extension': file_path.suffix.lower(),
            'size': stat.st_size,
            'size_human': self._format_file_size(stat.st_size),
            'modified_time': stat.st_mtime,
            'modified_date': self._format_timestamp(stat.st_mtime),
            'relative_path': str(file_path.relative_to(self.workspace_root)),
            'relevance_score': self._calculate_relevance_score(file_path, stat)
        }

    def _calculate_relevance_score(self, file_path: Path, stat) -> float:
        """Calculate relevance score for file prioritization."""
        score = 0.0

        # Base score by file type
        extension_scores = {
            '.pdf': 1.0,   # Highest priority - likely documentation
            '.docx': 0.9,  # Word docs often contain requirements
            '.xlsx': 0.8,  # Spreadsheets with data
            '.xls': 0.7,
            '.csv': 0.6,   # Data files
            '.md': 0.8,    # Markdown docs
            '.txt': 0.5,   # Plain text
            '.json': 0.4,  # Config/data files
            '.yaml': 0.4,
            '.yml': 0.4
        }

        score += extension_scores.get(file_path.suffix.lower(), 0.1)

        # Recency bonus (files modified in last 30 days get higher score)
        import time
        days_since_modified = (time.time() - stat.st_mtime) / (24 * 3600)
        if days_since_modified < 30:
            score += 0.3
        elif days_since_modified < 7:
            score += 0.5

        # Size bonus (medium-sized files are likely more relevant)
        size_mb = stat.st_size / (1024 * 1024)
        if 0.1 <= size_mb <= 10:  # 100KB to 10MB
            score += 0.2

        # Path-based scoring
        path_str = str(file_path).lower()
        if any(keyword in path_str for keyword in ['doc', 'docs', 'document', 'requirement', 'spec']):
            score += 0.3
        if any(keyword in path_str for keyword in ['readme', 'guide', 'manual']):
            score += 0.2

        return min(score, 2.0)  # Cap at 2.0

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return ".1f"
            size_bytes /= 1024.0
        return ".1f"

    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as readable date."""
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def get_file_summary(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics of detected files."""
        if not files:
            return {"total_files": 0, "total_size": 0, "types": {}}

        total_size = sum(f['size'] for f in files)
        types = {}
        for file in files:
            ext = file['extension']
            types[ext] = types.get(ext, 0) + 1

        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_human": self._format_file_size(total_size),
            "types": types,
            "top_files": sorted(files, key=lambda x: x['relevance_score'], reverse=True)[:5]
        }