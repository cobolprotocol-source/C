"""
COBOL Benchmarking - Dataset Generation Orchestrator

Coordinates deterministic generation of all benchmark datasets.
"""

import logging
import sys
from pathlib import Path
from typing import Dict

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    DATASETS_DIR, DATASET_TYPES, DATASET_SIZES, SEEDS,
    OutputConfig, LoggingConfig, create_directories
)
from datasets.generator import DatasetManifest
from datasets.generators import get_generator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format=LoggingConfig.LOG_FORMAT
)
logger = logging.getLogger(__name__)


def generate_all_datasets(skip_existing: bool = True) -> Dict:
    """Generate all benchmark datasets.
    
    Args:
        skip_existing: If True, skip datasets that already exist
        
    Returns:
        Dictionary of generated dataset metadata
    """
    logger.info("=" * 80)
    logger.info("COBOL PROTOCOL - BENCHMARK DATASET GENERATION")
    logger.info("=" * 80)
    
    create_directories()
    manifest = DatasetManifest(OutputConfig.MANIFEST)
    
    # Try to load existing manifest
    if skip_existing and manifest.load():
        logger.info(f"Loaded existing manifest with {len(manifest.datasets)} datasets")
        
        # Verify all datasets still exist
        verification = manifest.verify_all()
        missing = [k for k, v in verification.items() if not v]
        
        if missing:
            logger.warning(f"Found {len(missing)} datasets with checksum issues")
            logger.info("Regenerating affected datasets...")
        else:
            logger.info("✅ All datasets verified successfully")
            return manifest.datasets
    
    # Generate datasets
    total_size = 0
    dataset_count = 0
    
    for dataset_type in DATASET_TYPES:
        logger.info(f"\nGenerating {dataset_type}...")
        
        seed = SEEDS.get(dataset_type, 42)
        generator = get_generator(dataset_type, seed)
        
        for size_label, size_bytes in DATASET_SIZES.items():
            # Skip 1GB if not enough space
            if size_bytes >= 1024 * 1024 * 1024:  # 1GB
                try:
                    import psutil
                    available = psutil.disk_usage("/").free
                    if available < size_bytes * 2:
                        logger.warning(f"Skipping {size_label} ({size_bytes/1024/1024:.0f}MB) "
                                     f"- insufficient disk space")
                        continue
                except ImportError:
                    logger.warning("psutil not available, skipping disk check")
            
            output_dir = DATASETS_DIR / dataset_type
            output_file = output_dir / f"{size_label}.bin"
            
            # Check if already exists and valid
            if skip_existing and output_file.exists():
                logger.debug(f"Dataset {output_file.name} already exists, verifying...")
                if generator.verify_dataset(output_file):
                    logger.info(f"✓ Skipping {dataset_type}/{size_label}")
                    # Add to manifest
                    metadata = {
                        "path": str(output_file),
                        "size_bytes": size_bytes,
                        "size_readable": generator._format_size(size_bytes),
                        "dataset_type": dataset_type,
                        "seed": seed
                    }
                    manifest.add_dataset(metadata)
                    dataset_count += 1
                    total_size += size_bytes
                    continue
            
            # Generate dataset
            logger.info(f"Generating {dataset_type}/{size_label}...")
            data = generator.generate(size_bytes, output_file)
            metadata = generator.save_dataset(data, output_file)
            
            manifest.add_dataset(metadata)
            dataset_count += 1
            total_size += size_bytes
    
    # Save manifest
    manifest.save()
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ DATASET GENERATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Datasets generated: {dataset_count}")
    logger.info(f"Total size: {_format_size(total_size)}")
    logger.info(f"Manifest location: {OutputConfig.MANIFEST}")
    
    return manifest.datasets


def verify_datasets() -> bool:
    """Verify integrity of all existing datasets.
    
    Returns:
        True if all datasets are valid, False otherwise
    """
    logger.info("Verifying datasets...")
    
    manifest = DatasetManifest(OutputConfig.MANIFEST)
    if not manifest.load():
        logger.error("No manifest found")
        return False
    
    verification = manifest.verify_all()
    
    valid = sum(1 for v in verification.values() if v)
    total = len(verification)
    
    logger.info(f"Verification: {valid}/{total} datasets valid")
    
    for key, is_valid in verification.items():
        status = "✓" if is_valid else "✗"
        logger.info(f"  {status} {key}")
    
    return all(verification.values())


# Helper for size formatting in manifest
class _ManifestHelper:
    @staticmethod
    def _format_size_static(size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

DatasetManifest._format_size_static = _ManifestHelper._format_size_static


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="COBOL Benchmark Dataset Generator"
    )
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate all datasets (ignore existing)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing datasets only"
    )
    
    args = parser.parse_args()
    
    if args.verify:
        success = verify_datasets()
        sys.exit(0 if success else 1)
    else:
        datasets = generate_all_datasets(skip_existing=not args.regenerate)
        logger.info(f"Generated {len(datasets)} datasets")
