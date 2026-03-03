"""
COBOL Protocol Benchmarking - Dataset Generation Framework

Provides deterministic, reproducible dataset generation for benchmarking.
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class DatasetGenerator(ABC):
    """Abstract base class for all dataset generators."""
    
    def __init__(self, dataset_type: str, seed: int):
        """Initialize generator.
        
        Args:
            dataset_type: Type identifier (e.g., "text_log_repetitive")
            seed: Deterministic seed for reproducibility
        """
        self.dataset_type = dataset_type
        self.seed = seed
        self.generated_files = []
    
    @abstractmethod
    def generate(self, size: int, output_path: Path) -> bytes:
        """Generate dataset of specified size.
        
        Args:
            size: Number of bytes to generate
            output_path: Where to save the dataset
            
        Returns:
            Generated data as bytes (for verification)
        """
        pass
    
    def calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA256 checksum of data.
        
        Args:
            data: Bytes to checksum
            
        Returns:
            Hex-formatted SHA256 hash
        """
        return hashlib.sha256(data).hexdigest()
    
    def save_dataset(self, data: bytes, output_path: Path) -> Dict:
        """Save dataset to file with metadata.
        
        Args:
            data: Generated data
            output_path: Where to save
            
        Returns:
            Metadata dictionary
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write data
        with open(output_path, 'wb') as f:
            f.write(data)
        
        # Calculate checksum
        checksum = self.calculate_checksum(data)
        
        # Save checksum
        checksum_path = Path(f"{output_path}.sha256")
        with open(checksum_path, 'w') as f:
            f.write(checksum)
        
        metadata = {
            "path": str(output_path),
            "size_bytes": len(data),
            "size_readable": self._format_size(len(data)),
            "sha256": checksum,
            "dataset_type": self.dataset_type,
            "seed": self.seed
        }
        
        logger.info(f"Generated {self.dataset_type} ({metadata['size_readable']}) "
                   f"to {output_path.name}")
        logger.debug(f"  SHA256: {checksum}")
        
        self.generated_files.append(metadata)
        return metadata
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
    
    def verify_dataset(self, file_path: Path) -> bool:
        """Verify dataset integrity by checking checksum.
        
        Args:
            file_path: Path to dataset file
            
        Returns:
            True if checksum matches, False otherwise
        """
        checksum_path = Path(f"{file_path}.sha256")
        
        if not checksum_path.exists():
            logger.warning(f"No checksum file for {file_path}")
            return False
        
        # Read stored checksum
        with open(checksum_path, 'r') as f:
            stored_checksum = f.read().strip()
        
        # Calculate current checksum
        with open(file_path, 'rb') as f:
            data = f.read()
        current_checksum = self.calculate_checksum(data)
        
        if stored_checksum == current_checksum:
            logger.debug(f"✓ Dataset {file_path.name} verified")
            return True
        else:
            logger.error(f"✗ Checksum mismatch for {file_path.name}")
            logger.error(f"  Expected: {stored_checksum}")
            logger.error(f"  Got:      {current_checksum}")
            return False


class DatasetManifest:
    """Manages dataset registry and verification."""
    
    def __init__(self, manifest_path: Path):
        """Initialize manifest.
        
        Args:
            manifest_path: Path to manifest.json
        """
        self.manifest_path = manifest_path
        self.datasets = {}
    
    def add_dataset(self, metadata: Dict):
        """Add dataset to manifest.
        
        Args:
            metadata: Dataset metadata dictionary
        """
        key = f"{metadata['dataset_type']}_{metadata['size_bytes']}"
        self.datasets[key] = metadata
    
    def save(self):
        """Save manifest to file."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.manifest_path, 'w') as f:
            json.dump({
                "datasets": self.datasets,
                "total_datasets": len(self.datasets),
                "total_size_bytes": sum(d['size_bytes'] for d in self.datasets.values())
            }, f, indent=2)
        
        logger.info(f"Manifest saved: {self.manifest_path}")
    
    def load(self) -> bool:
        """Load manifest from file.
        
        Returns:
            True if loaded successfully, False if file doesn't exist
        """
        if not self.manifest_path.exists():
            return False
        
        with open(self.manifest_path, 'r') as f:
            data = json.load(f)
            self.datasets = data.get('datasets', {})
        
        logger.info(f"Manifest loaded: {len(self.datasets)} datasets")
        return True
    
    def verify_all(self) -> Dict[str, bool]:
        """Verify all datasets.
        
        Returns:
            Dictionary mapping dataset keys to verification results
        """
        results = {}
        for key, metadata in self.datasets.items():
            file_path = Path(metadata['path'])
            if file_path.exists():
                with open(file_path, 'rb') as f:
                    data = f.read()
                current_checksum = hashlib.sha256(data).hexdigest()
                results[key] = current_checksum == metadata['sha256']
            else:
                results[key] = False
        
        return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"


if __name__ == "__main__":
    print("Dataset Generator Framework loaded successfully")
