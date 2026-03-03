"""
Specific Dataset Generators for COBOL Benchmarking

Each generator creates deterministic data of specified types and sizes.
"""

import random
import json
from datetime import datetime, timedelta
from pathlib import Path

from ..generator import DatasetGenerator


class TextLogRepetitiveGenerator(DatasetGenerator):
    """Generates repetitive text log data (highly compressible).
    
    Simulates typical server logs with repeated patterns:
    - Timestamps
    - Log levels
    - Service names
    - Message templates
    """
    
    def generate(self, size: int, output_path: Path) -> bytes:
        """Generate repetitive log data."""
        random.seed(self.seed)
        
        # Log templates
        templates = [
            "[{timestamp}] {level} {service}: {message}",
            "{timestamp} - {service} - {level}: {message}",
            "{timestamp}|{level}|{service}|{message}",
        ]
        
        levels = ["INFO", "DEBUG", "WARN", "ERROR"]
        services = ["web-app", "db-server", "cache", "queue", "auth-svc"]
        messages = [
            "Request processed successfully",
            "Database connection established",
            "Cache hit",
            "Queue message processed",
            "Authentication successful",
            "Request timeout",
            "Database query executed",
            "Cache miss",
            "Error occurred",
        ]
        
        data = bytearray()
        start_time = datetime(2026, 3, 1, 0, 0, 0)
        
        log_count = 0
        while len(data) < size:
            # Generate log entry
            timestamp = (start_time + timedelta(seconds=log_count)).isoformat()
            level = random.choice(levels)
            service = random.choice(services)
            message = random.choice(messages)
            
            template = random.choice(templates)
            log_line = template.format(
                timestamp=timestamp,
                level=level,
                service=service,
                message=message
            ) + "\n"
            
            data.extend(log_line.encode())
            log_count += 1
        
        return bytes(data[:size])


class JsonTelemetryGenerator(DatasetGenerator):
    """Generates JSON telemetry data (structured, semi-repetitive).
    
    Simulates IoT sensor or application telemetry:
    - Timestamps
    - Device IDs
    - Metric names
    - Values
    """
    
    def generate(self, size: int, output_path: Path) -> bytes:
        """Generate JSON telemetry data."""
        random.seed(self.seed)
        
        device_ids = [f"device-{i:05d}" for i in range(1, 101)]
        metrics = ["temperature", "humidity", "pressure", "cpu_usage", "memory_usage"]
        
        data = bytearray()
        timestamp = datetime(2026, 3, 1, 0, 0, 0)
        
        entry_count = 0
        while len(data) < size:
            device_id = random.choice(device_ids)
            metric = random.choice(metrics)
            value = round(random.uniform(0, 100), 2)
            
            entry = {
                "device_id": device_id,
                "metric": metric,
                "value": value,
                "unit": "%" if "usage" in metric else "C" if "temperature" in metric else "",
                "timestamp": timestamp.isoformat(),
                "sequence": entry_count
            }
            
            entry_json = json.dumps(entry, separators=(',', ':')) + "\n"
            data.extend(entry_json.encode())
            
            timestamp += timedelta(seconds=1)
            entry_count += 1
        
        return bytes(data[:size])


class MixedTextBinaryGenerator(DatasetGenerator):
    """Generates mixed text and binary data (medium compressibility).
    
    Simulates real-world mixed workloads:
    - 60% text (logs, JSON)
    - 40% binary (partial compression, image headers, etc.)
    """
    
    def generate(self, size: int, output_path: Path) -> bytes:
        """Generate mixed text and binary data."""
        random.seed(self.seed)
        
        text_size = int(size * 0.6)
        binary_size = size - text_size
        
        # Generate text portion
        text_data = bytearray()
        while len(text_data) < text_size:
            line = f"Log entry {len(text_data)} - some text content\n"
            text_data.extend(line.encode())
        
        # Generate binary portion
        binary_data = bytearray(
            random.randint(0, 255) for _ in range(binary_size)
        )
        
        # Interleave text and binary
        combined = bytearray()
        chunk_size = 4096
        
        text_offset = 0
        binary_offset = 0
        
        while text_offset < text_size or binary_offset < binary_size:
            # Add text chunk
            if text_offset < text_size:
                end = min(text_offset + chunk_size, text_size)
                combined.extend(text_data[text_offset:end])
                text_offset = end
            
            # Add binary chunk
            if binary_offset < binary_size:
                end = min(binary_offset + chunk_size, binary_size)
                combined.extend(binary_data[binary_offset:end])
                binary_offset = end
        
        return bytes(combined[:size])


class HighEntropyRandomGenerator(DatasetGenerator):
    """Generates high-entropy random data (incompressible).
    
    Simulates:
    - Encrypted data
    - Already-compressed data
    - Cryptographic material
    """
    
    def generate(self, size: int, output_path: Path) -> bytes:
        """Generate high-entropy random data."""
        random.seed(self.seed)
        
        # Generate truly random bytes
        data = bytearray(
            random.randint(0, 255) for _ in range(size)
        )
        
        return bytes(data)


# ============================================================================
# GENERATOR REGISTRY
# ============================================================================

GENERATORS = {
    "text_log_repetitive": TextLogRepetitiveGenerator,
    "json_telemetry": JsonTelemetryGenerator,
    "mixed_text_binary": MixedTextBinaryGenerator,
    "high_entropy_random": HighEntropyRandomGenerator,
}


def get_generator(dataset_type: str, seed: int) -> DatasetGenerator:
    """Get generator instance for dataset type.
    
    Args:
        dataset_type: Type of dataset to generate
        seed: Deterministic seed
        
    Returns:
        Generator instance
        
    Raises:
        ValueError: If dataset_type is unknown
    """
    if dataset_type not in GENERATORS:
        raise ValueError(f"Unknown dataset type: {dataset_type}")
    
    generator_class = GENERATORS[dataset_type]
    return generator_class(dataset_type, seed)


if __name__ == "__main__":
    print("Dataset generators loaded successfully")
