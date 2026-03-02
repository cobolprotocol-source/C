#!/usr/bin/env python3
"""
COBOL Protocol v1.5.3 - Performance Profile System

Single-source-of-truth implementation for performance profiles.
This module is the reference implementation for all language bindings.

Key principles:
- Profiles are STATIC and IMMUTABLE at runtime
- Profiles do NOT affect file format, decompression, crypto, or DP guarantees
- AUTO selection is DETERMINISTIC and based on hardware inspection ONLY
- Fallback is SAFE, BOUNDED, and LOGGED

All parameters come from spec/performance_profiles.yaml
No language may hardcode profile parameters.
"""

import os
import json
import yaml
import logging
import platform
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class CompressionDepth(Enum):
    """Compression depth levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    MAX = "MAX"


class PipelineMode(Enum):
    """Pipeline processing modes"""
    SERIAL = "serial"
    SEMI_PARALLEL = "semi_parallel"
    PARALLEL = "parallel"
    DEEP_PARALLEL = "deep_parallel"


class ProfileName(Enum):
    """Available performance profiles (exactly 5)"""
    EDGE_LOW = "EDGE_LOW"
    CLIENT_STANDARD = "CLIENT_STANDARD"
    WORKSTATION_PRO = "WORKSTATION_PRO"
    SERVER_GENERAL = "SERVER_GENERAL"
    DATACENTER_HIGH = "DATACENTER_HIGH"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ProfileParameters:
    """Parameters for a performance profile (loaded from YAML)"""
    chunk_size_bytes: int
    compression_depth: str
    pipeline_mode: str
    aes_batch_size: int
    aes_threads: int
    dp_window_seconds: int
    dp_epsilon_default: float
    fallback_latency_threshold_ms: int
    
    def validate(self) -> bool:
        """Validate parameter ranges"""
        assert 4096 <= self.chunk_size_bytes <= 2097152
        assert self.compression_depth in ["LOW", "MEDIUM", "HIGH", "MAX"]
        assert self.pipeline_mode in ["serial", "semi_parallel", "parallel", "deep_parallel"]
        assert 1 <= self.aes_batch_size <= 2048
        assert 1 <= self.aes_threads <= 256
        assert 1 <= self.dp_window_seconds <= 300
        assert 0.01 <= self.dp_epsilon_default <= 1.0
        assert 10 <= self.fallback_latency_threshold_ms <= 5000
        return True


@dataclass
class ProfileDefinition:
    """Complete profile definition"""
    name: str
    description: str
    target_environments: List[str]
    constraints: Dict[str, Any]
    parameters: ProfileParameters
    characteristics: Dict[str, Any]
    notes: Optional[str] = None


@dataclass
class HardwareInfo:
    """Hardware characteristics for AUTO selection"""
    cpu_cores: int
    total_memory_gb: int
    l3_cache_mb: Optional[int] = None
    aes_ni_available: bool = False
    numa_present: bool = False
    
    @staticmethod
    def detect() -> 'HardwareInfo':
        """Detect hardware characteristics (deterministic, timing-independent)"""
        import psutil
        
        cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True) or 1
        total_memory_gb = int(psutil.virtual_memory().total / (1024 ** 3))
        
        # AES-NI detection (safe, deterministic)
        aes_ni_available = False
        try:
            import subprocess
            # Linux/Unix check
            result = subprocess.run(
                ['grep', '-i', 'aes', '/proc/cpuinfo'],
                capture_output=True,
                timeout=1
            )
            aes_ni_available = result.returncode == 0
        except:
            # Windows or other platform
            try:
                import subprocess
                result = subprocess.run(
                    ['wmic', 'cpu', 'get', 'Description'],
                    capture_output=True,
                    timeout=1,
                    shell=True
                )
                aes_ni_available = 'AES' in result.stdout.decode()
            except:
                pass
        
        # NUMA detection (optional, safe)
        numa_present = False
        try:
            numa_present = os.path.exists('/sys/devices/virtual/dmi/id/') and \
                          any('node' in d for d in os.listdir('/sys/devices/system/node/'))
        except:
            pass
        
        return HardwareInfo(
            cpu_cores=cpu_cores,
            total_memory_gb=total_memory_gb,
            aes_ni_available=aes_ni_available,
            numa_present=numa_present
        )


@dataclass
class ProfileSelection:
    """Result of AUTO profile selection"""
    profile_name: str
    justification: str
    hardware_info: HardwareInfo
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def is_same_as(self, other: 'ProfileSelection') -> bool:
        """Check if selection is identical (for determinism testing)"""
        return (
            self.profile_name == other.profile_name and
            self.hardware_info.cpu_cores == other.hardware_info.cpu_cores and
            self.hardware_info.total_memory_gb == other.hardware_info.total_memory_gb
        )


# ============================================================================
# PERFORMANCE PROFILE MANAGER
# ============================================================================

class PerformanceProfileManager:
    """
    Single-source-of-truth manager for performance profiles.
    
    CRITICAL DESIGN:
    - All profile data loaded from YAML spec file
    - No hardcoding of parameters in code
    - Deterministic AUTO selection based on hardware
    - Safe fallback with bounded downgrade
    - Language-independent FFI contract
    """
    
    def __init__(self, spec_path: Optional[str] = None):
        """
        Initialize profile manager
        
        Args:
            spec_path: Path to performance_profiles.yaml (auto-detected if None)
        """
        self.spec_path = spec_path or self._find_spec()
        self.spec = self._load_spec()
        self.profiles: Dict[str, ProfileDefinition] = {}
        self._load_profiles()
        
        self.active_profile: Optional[str] = None
        self.active_profile_selection: Optional[ProfileSelection] = None
        self.fallback_history: List[Tuple[str, str, str]] = []  # (from, to, reason)
        
        logger.info(f"PerformanceProfileManager initialized (spec: {self.spec_path})")
    
    # ──────────────────────────────────────────────────────────────────────
    # SPEC LOADING
    # ──────────────────────────────────────────────────────────────────────
    
    def _find_spec(self) -> str:
        """Find spec file (auto-detect location)"""
        candidates = [
            Path(__file__).parent / "spec" / "performance_profiles.yaml",
            Path.cwd() / "spec" / "performance_profiles.yaml",
            Path.home() / ".cobol" / "spec" / "performance_profiles.yaml",
        ]
        
        for path in candidates:
            if path.exists():
                logger.debug(f"Found spec file: {path}")
                return str(path)
        
        raise FileNotFoundError(
            f"Could not find performance_profiles.yaml. "
            f"Searched: {[str(p) for p in candidates]}"
        )
    
    def _load_spec(self) -> Dict[str, Any]:
        """Load and validate specification from YAML"""
        with open(self.spec_path, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Validate spec version and format
        assert spec.get('spec_version') == "1.0", "Spec version mismatch"
        assert spec.get('format_version') == "1.5.3", "Format version mismatch"
        
        logger.debug(f"Loaded spec v{spec['spec_version']} (format {spec['format_version']})")
        return spec
    
    def _load_profiles(self):
        """Load profile definitions from spec"""
        for profile_name, profile_data in self.spec['profiles'].items():
            params = ProfileParameters(
                chunk_size_bytes=profile_data['parameters']['chunk_size_bytes'],
                compression_depth=profile_data['parameters']['compression_depth'],
                pipeline_mode=profile_data['parameters']['pipeline_mode'],
                aes_batch_size=profile_data['parameters']['aes_batch_size'],
                aes_threads=profile_data['parameters']['aes_threads'],
                dp_window_seconds=profile_data['parameters']['dp_window_seconds'],
                dp_epsilon_default=profile_data['parameters']['dp_epsilon_default'],
                fallback_latency_threshold_ms=profile_data['parameters']['fallback_latency_threshold_ms']
            )
            
            # Validate parameters
            assert params.validate(), f"Invalid parameters for {profile_name}"
            
            profile = ProfileDefinition(
                name=profile_name,
                description=profile_data['description'],
                target_environments=profile_data['target_environments'],
                constraints=profile_data.get('constraints', {}),
                parameters=params,
                characteristics=profile_data['characteristics'],
                notes=profile_data.get('notes')
            )
            
            self.profiles[profile_name] = profile
        
        assert len(self.profiles) == 5, "Must have exactly 5 profiles"
        logger.debug(f"Loaded {len(self.profiles)} profiles")
    
    # ──────────────────────────────────────────────────────────────────────
    # AUTO SELECTION (DETERMINISTIC)
    # ──────────────────────────────────────────────────────────────────────
    
    def auto_select_profile(self, hardware_info: Optional[HardwareInfo] = None) -> ProfileSelection:
        """
        AUTO-select profile based on hardware characteristics.
        
        DETERMINISTIC: Same hardware + same version always selects same profile
        NO BENCHMARKING: Pure hardware inspection, no stress tests
        EXPLAINABLE: Provides human-readable justification
        
        Args:
            hardware_info: Hardware characteristics (auto-detected if None)
        
        Returns:
            ProfileSelection with profile name and justification
        """
        if hardware_info is None:
            hardware_info = HardwareInfo.detect()
        
        selected_profile = self._apply_selection_rules(hardware_info)
        justification = self._format_justification(selected_profile, hardware_info)
        
        selection = ProfileSelection(
            profile_name=selected_profile,
            justification=justification,
            hardware_info=hardware_info
        )
        
        logger.info(f"AUTO: {justification}")
        return selection
    
    def _apply_selection_rules(self, hardware: HardwareInfo) -> str:
        """Apply AUTO selection rules in priority order"""
        rules = self.spec['auto_selection_rules']
        
        # Sort by priority (descending)
        sorted_rules = sorted(
            rules.items(),
            key=lambda x: x[1]['priority'],
            reverse=True
        )
        
        for rule_name, rule in sorted_rules:
            if self._matches_conditions(rule['conditions'], hardware):
                return rule['selected_profile']
        
        # Fallback (should never reach this)
        logger.warning("No AUTO rule matched, defaulting to CLIENT_STANDARD")
        return ProfileName.CLIENT_STANDARD.value
    
    def _matches_conditions(self, conditions: List[str], hardware: HardwareInfo) -> bool:
        """Check if hardware matches all conditions"""
        for condition in conditions:
            if not self._eval_condition(condition, hardware):
                return False
        return True
    
    def _eval_condition(self, condition: str, hw: HardwareInfo) -> bool:
        """Evaluate a single condition (safe, no code injection)"""
        # Parse condition: "cpu_cores >= 64" or "aes_ni_available: true"
        
        if ">=" in condition:
            var, val = condition.split(">=")
            var = var.strip()
            val = int(val.strip())
            return getattr(hw, var, 0) >= val
        
        elif "<=" in condition:
            var, val = condition.split("<=")
            var = var.strip()
            val = int(val.strip())
            return getattr(hw, var, 0) <= val
        
        elif ":" in condition:
            # Boolean condition: "aes_ni_available: true"
            var, val = condition.split(":")
            var = var.strip()
            val = val.strip().lower() == 'true'
            return getattr(hw, var, False) == val
        
        else:
            logger.warning(f"Could not parse condition: {condition}")
            return False
    
    def _format_justification(self, profile_name: str, hw: HardwareInfo) -> str:
        """Format human-readable justification"""
        rules = self.spec['auto_selection_rules']
        
        for rule_name, rule in rules.items():
            if rule['selected_profile'] == profile_name:
                template = rule['justification_template']
                return template.format(
                    cores=hw.cpu_cores,
                    memory=hw.total_memory_gb
                )
        
        return f"Selected {profile_name} (reason unknown)"
    
    # ──────────────────────────────────────────────────────────────────────
    # PROFILE MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────
    
    def set_profile(self, profile_name: str) -> bool:
        """
        Set active profile (may be forced by user or selected by AUTO)
        
        Args:
            profile_name: Profile name (must be one of 5 defined profiles)
        
        Returns:
            True if set successfully
        
        Raises:
            ValueError if invalid profile name
        """
        if profile_name not in self.profiles:
            raise ValueError(
                f"Unknown profile: {profile_name}. "
                f"Valid profiles: {list(self.profiles.keys())}"
            )
        
        self.active_profile = profile_name
        logger.info(f"Set profile: {profile_name}")
        return True
    
    def get_active_profile(self) -> str:
        """Get currently active profile name"""
        if self.active_profile is None:
            raise RuntimeError("No profile selected. Call auto_select_profile() or set_profile()")
        return self.active_profile
    
    def get_profile_parameters(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get parameters for a profile
        
        Args:
            profile_name: Profile name (uses active if None)
        
        Returns:
            Dictionary of parameters
        """
        if profile_name is None:
            profile_name = self.get_active_profile()
        
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")
        
        profile = self.profiles[profile_name]
        return asdict(profile.parameters)
    
    def get_profile_definition(self, profile_name: Optional[str] = None) -> ProfileDefinition:
        """Get complete profile definition"""
        if profile_name is None:
            profile_name = self.get_active_profile()
        
        return self.profiles[profile_name]
    
    def explain_profile_selection(self) -> str:
        """Get explanation of current profile selection"""
        if self.active_profile_selection is None:
            return "No profile selection explanation available"
        return self.active_profile_selection.justification
    
    # ──────────────────────────────────────────────────────────────────────
    # SAFE FALLBACK
    # ──────────────────────────────────────────────────────────────────────
    
    def safe_fallback(self, reason: str, measured_latency_ms: float) -> bool:
        """
        Safely downgrade to lower profile (ONLY ONE LEVEL)
        
        Fallback is allowed when:
        - Latency exceeds profile threshold
        - Memory pressure detected
        
        Args:
            reason: Reason for fallback (logged)
            measured_latency_ms: Measured latency in milliseconds
        
        Returns:
            True if fallback was applied, False if already at minimum
        """
        current = self.get_active_profile()
        
        # Get fallback chain
        chain = self.spec['fallback_rules']['chain']
        next_profile = chain.get(current)
        
        if next_profile is None or next_profile == current:
            logger.warning(f"Cannot fallback from {current} (already at minimum)")
            return False
        
        # Log fallback
        log_msg = f"FALLBACK: {current} -> {next_profile} (reason: {reason}, latency: {measured_latency_ms:.1f}ms)"
        logger.warning(log_msg)
        
        self.fallback_history.append((current, next_profile, reason))
        self.set_profile(next_profile)
        
        return True
    
    def get_fallback_history(self) -> List[Tuple[str, str, str]]:
        """Get history of fallbacks (from, to, reason)"""
        return self.fallback_history.copy()
    
    # ──────────────────────────────────────────────────────────────────────
    # VALIDATION & TESTING
    # ──────────────────────────────────────────────────────────────────────
    
    def validate_spec(self) -> bool:
        """Validate specification against schema"""
        try:
            with open(Path(self.spec_path).parent / "profile_schema.json") as f:
                schema = json.load(f)
            
            # Use jsonschema if available
            try:
                import jsonschema
                jsonschema.validate(self.spec, schema)
                logger.info("Spec validation: OK")
                return True
            except ImportError:
                # Fallback: just check required keys
                required = ['spec_version', 'format_version', 'profiles', 'auto_selection_rules']
                if all(k in self.spec for k in required):
                    logger.info("Spec validation: OK (basic)")
                    return True
                else:
                    logger.error("Spec validation: FAILED")
                    return False
        except Exception as e:
            logger.error(f"Spec validation failed: {e}")
            return False
    
    def test_auto_determinism(self, iterations: int = 10) -> bool:
        """
        Test that AUTO selection is deterministic
        
        Same hardware profile should always select same profile
        """
        hw = HardwareInfo.detect()
        
        selections = [self.auto_select_profile(hw) for _ in range(iterations)]
        first = selections[0]
        
        for selection in selections[1:]:
            if not selection.is_same_as(first):
                logger.error("AUTO selection is NOT deterministic")
                return False
        
        logger.info(f"AUTO determinism: OK ({iterations} iterations)")
        return True
    
    def test_fallback_determinism(self) -> bool:
        """Test that fallback is deterministic"""
        chain = self.spec['fallback_rules']['chain']
        
        for profile, fallback in chain.items():
            if fallback == profile:
                # No fallback (at minimum)
                continue
            
            # Check that fallback is consistent
            if profile not in self.profiles or fallback not in self.profiles:
                logger.error(f"Invalid fallback chain: {profile} -> {fallback}")
                return False
        
        logger.info("Fallback determinism: OK")
        return True
    
    def print_profile_info(self, profile_name: Optional[str] = None):
        """Pretty-print profile information"""
        if profile_name is None:
            profile_name = self.get_active_profile()
        
        profile = self.profiles[profile_name]
        
        print(f"\nProfile: {profile_name}")
        print(f"Description: {profile.description}")
        print(f"Target: {', '.join(profile.target_environments)}")
        print(f"\nParameters:")
        for key, value in asdict(profile.parameters).items():
            print(f"  {key}: {value}")
        print(f"\nCharacteristics:")
        for key, value in profile.characteristics.items():
            print(f"  {key}: {value}")
        if profile.notes:
            print(f"\nNotes: {profile.notes}")


# ============================================================================
# GLOBAL INSTANCE (FFI CONTRACT)
# ============================================================================

_manager: Optional[PerformanceProfileManager] = None


def initialize_profiles(spec_path: Optional[str] = None):
    """Initialize global profile manager (must call once)"""
    global _manager
    _manager = PerformanceProfileManager(spec_path)


def ensure_initialized():
    """Ensure manager is initialized"""
    global _manager
    if _manager is None:
        _manager = PerformanceProfileManager()


# ============================================================================
# FFI API (LANGUAGE BINDINGS USE THESE)
# ============================================================================

def set_profile(profile_name: str) -> bool:
    """FFI: Set active profile"""
    ensure_initialized()
    return _manager.set_profile(profile_name)


def auto_select_profile() -> str:
    """FFI: AUTO-select profile, return name"""
    ensure_initialized()
    selection = _manager.auto_select_profile()
    _manager.active_profile_selection = selection
    _manager.set_profile(selection.profile_name)
    return selection.profile_name


def get_active_profile() -> str:
    """FFI: Get active profile name"""
    ensure_initialized()
    return _manager.get_active_profile()


def get_profile_parameters() -> Dict[str, Any]:
    """FFI: Get parameters for active profile"""
    ensure_initialized()
    return _manager.get_profile_parameters()


def explain_profile_selection() -> str:
    """FFI: Get explanation of profile selection"""
    ensure_initialized()
    return _manager.explain_profile_selection()


def get_manager() -> PerformanceProfileManager:
    """Get global manager instance (for tests)"""
    ensure_initialized()
    return _manager


# ============================================================================
# MAIN / TESTING
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("Performance Profile System - Test")
    print("=" * 80)
    
    # Initialize
    initialize_profiles()
    manager = get_manager()
    
    # Validate spec
    print("\n[1/5] Validating specification...")
    assert manager.validate_spec(), "Spec validation failed"
    print("  ✓ Spec validation passed")
    
    # AUTO select
    print("\n[2/5] AUTO-selecting profile...")
    selection = manager.auto_select_profile()
    manager.set_profile(selection.profile_name)
    print(f"  ✓ Selected: {selection.profile_name}")
    print(f"  ✓ Reason: {selection.justification}")
    
    # Test determinism
    print("\n[3/5] Testing AUTO determinism...")
    assert manager.test_auto_determinism(5), "AUTO not deterministic"
    print("  ✓ AUTO determinism verified")
    
    # Test fallback
    print("\n[4/5] Testing fallback mechanism...")
    assert manager.test_fallback_determinism(), "Fallback not deterministic"
    print("  ✓ Fallback mechanism verified")
    
    # Print profile info
    print("\n[5/5] Profile information:")
    manager.print_profile_info()
    
    print("\n" + "=" * 80)
    print("✓ All tests passed")
    print("=" * 80)
