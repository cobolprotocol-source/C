"""
Dataset Manifest Management for COBOL Benchmarks

Provides functions to load and query the dataset manifest.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_manifest(manifest_path: Path) -> Optional[List[Dict[str, Any]]]:
    """Load dataset manifest from JSON file.
    
    Args:
        manifest_path: Path to manifest.json
        
    Returns:
        List of dataset metadata dicts, or None if not found
    """
    if not manifest_path.exists():
        return None
    
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        # Handle both formats: {"datasets": [...]} or [...]
        if isinstance(data, dict) and "datasets" in data:
            return data["datasets"]
        elif isinstance(data, list):
            return data
        else:
            return None
    except Exception as e:
        print(f"Error loading manifest: {e}")
        return None


def get_dataset_by_type(manifest: List[Dict], dataset_type: str) -> List[Dict]:
    """Get all datasets of a specific type.
    
    Args:
        manifest: List of dataset metadata
        dataset_type: Type to filter by (e.g., "text_log_repetitive")
        
    Returns:
        List of matching datasets
    """
    return [ds for ds in manifest if ds.get('dataset_type') == dataset_type]


def get_dataset_by_size(manifest: List[Dict], size_label: str) -> List[Dict]:
    """Get all datasets of a specific size.
    
    Args:
        manifest: List of dataset metadata
        size_label: Size label (e.g., "small", "medium", "large")
        
    Returns:
        List of matching datasets
    """
    return [ds for ds in manifest if ds.get('size_label') == size_label]


def get_largest_available_dataset(manifest: List[Dict]) -> Optional[Dict]:
    """Get the largest available dataset.
    
    Args:
        manifest: List of dataset metadata
        
    Returns:
        Largest dataset metadata, or None
    """
    if not manifest:
        return None
    
    return max(manifest, key=lambda ds: ds.get('size_bytes', 0))


def get_smallest_available_dataset(manifest: List[Dict]) -> Optional[Dict]:
    """Get the smallest available dataset.
    
    Args:
        manifest: List of dataset metadata
        
    Returns:
        Smallest dataset metadata, or None
    """
    if not manifest:
        return None
    
    return min(manifest, key=lambda ds: ds.get('size_bytes', float('inf')))
