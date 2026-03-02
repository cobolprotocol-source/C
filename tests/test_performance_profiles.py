#!/usr/bin/env python3
"""
Comprehensive test suite for Performance Profile System

Tests cover:
- Schema validation
- All 5 profile definitions
- AUTO selection determinism
- Forced profile override
- Safe fallback mechanism
- Cross-profile consistency
- Edge cases and error handling
"""

import pytest
import sys
import os
from pathlib import Path

# Add cwd to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.performance_profiles import (
    PerformanceProfileManager,
    HardwareInfo,
    ProfileName,
    CompressionDepth,
    PipelineMode,
    set_profile,
    auto_select_profile,
    get_active_profile,
    get_profile_parameters,
    explain_profile_selection,
    get_manager
)


class TestProfileSystem:
    """Test suite for performance profile system"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.manager = PerformanceProfileManager()
        yield
    
    # ──────────────────────────────────────────────────────────────────────
    # BASIC FUNCTIONALITY
    # ──────────────────────────────────────────────────────────────────────
    
    def test_exactly_5_profiles(self):
        """Verify exactly 5 profiles are defined"""
        assert len(self.manager.profiles) == 5
        expected = {
            'EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO',
            'SERVER_GENERAL', 'DATACENTER_HIGH'
        }
        assert set(self.manager.profiles.keys()) == expected
    
    def test_profile_names_match_enum(self):
        """Profile names must match ProfileName enum"""
        profile_names = set(self.manager.profiles.keys())
        enum_names = {p.value for p in ProfileName}
        assert profile_names == enum_names
    
    def test_spec_validation(self):
        """Specification must pass schema validation"""
        assert self.manager.validate_spec()
    
    # ──────────────────────────────────────────────────────────────────────
    # INDIVIDUAL PROFILE VALIDATION
    # ──────────────────────────────────────────────────────────────────────
    
    def test_edge_low_profile(self):
        """Verify EDGE_LOW profile"""
        profile = self.manager.profiles['EDGE_LOW']
        assert profile.name == 'EDGE_LOW'
        assert profile.parameters.chunk_size_bytes == 8192  # 8 KB
        assert profile.parameters.compression_depth == 'LOW'
        assert profile.parameters.pipeline_mode == 'serial'
        assert profile.parameters.aes_threads == 1
    
    def test_client_standard_profile(self):
        """Verify CLIENT_STANDARD profile"""
        profile = self.manager.profiles['CLIENT_STANDARD']
        assert profile.name == 'CLIENT_STANDARD'
        assert profile.parameters.chunk_size_bytes == 64000  # 64 KB
        assert profile.parameters.compression_depth == 'MEDIUM'
        assert profile.parameters.pipeline_mode == 'serial'
        # Should be safe fallback
        assert 'SAFE FALLBACK' in profile.notes or 'safe fallback' in profile.notes.lower()
    
    def test_workstation_pro_profile(self):
        """Verify WORKSTATION_PRO profile"""
        profile = self.manager.profiles['WORKSTATION_PRO']
        assert profile.name == 'WORKSTATION_PRO'
        assert profile.parameters.chunk_size_bytes == 256000  # 256 KB
        assert profile.parameters.compression_depth == 'HIGH'
        assert profile.parameters.pipeline_mode == 'semi_parallel'
    
    def test_server_general_profile(self):
        """Verify SERVER_GENERAL profile"""
        profile = self.manager.profiles['SERVER_GENERAL']
        assert profile.name == 'SERVER_GENERAL'
        assert profile.parameters.chunk_size_bytes == 512000  # 512 KB
        assert profile.parameters.compression_depth == 'HIGH'
        assert profile.parameters.pipeline_mode == 'parallel'
    
    def test_datacenter_high_profile(self):
        """Verify DATACENTER_HIGH profile"""
        profile = self.manager.profiles['DATACENTER_HIGH']
        assert profile.name == 'DATACENTER_HIGH'
        assert profile.parameters.chunk_size_bytes == 1048576  # 1 MB
        assert profile.parameters.compression_depth == 'MAX'
        assert profile.parameters.pipeline_mode == 'deep_parallel'
    
    def test_profile_characteristics(self):
        """All profiles must have valid characteristics"""
        for profile_name, profile in self.manager.profiles.items():
            assert 'max_throughput_mbps' in profile.characteristics
            assert 'memory_overhead_mb' in profile.characteristics
            assert 'cpu_utilization_percent' in profile.characteristics
            assert 'suitable_for' in profile.characteristics
            
            # Validate ranges
            assert profile.characteristics['max_throughput_mbps'] > 0
            assert profile.characteristics['memory_overhead_mb'] > 0
            assert 1 <= profile.characteristics['cpu_utilization_percent'] <= 100
    
    # ──────────────────────────────────────────────────────────────────────
    # PROFILE PROGRESSION
    # ──────────────────────────────────────────────────────────────────────
    
    def test_chunk_size_increases(self):
        """Chunk size should increase from EDGE to DATACENTER"""
        profiles_ordered = [
            'EDGE_LOW',
            'CLIENT_STANDARD',
            'WORKSTATION_PRO',
            'SERVER_GENERAL',
            'DATACENTER_HIGH'
        ]
        
        chunk_sizes = [
            self.manager.profiles[p].parameters.chunk_size_bytes
            for p in profiles_ordered
        ]
        
        # Should be monotonically increasing
        for i in range(len(chunk_sizes) - 1):
            assert chunk_sizes[i] < chunk_sizes[i + 1], \
                f"Chunk sizes not increasing: {chunk_sizes}"
    
    def test_aes_threads_increase(self):
        """AES threads should generally increase from EDGE to DATACENTER"""
        profiles_ordered = [
            'EDGE_LOW',
            'CLIENT_STANDARD',
            'WORKSTATION_PRO',
            'SERVER_GENERAL',
            'DATACENTER_HIGH'
        ]
        
        aes_threads = [
            self.manager.profiles[p].parameters.aes_threads
            for p in profiles_ordered
        ]
        
        # Should be monotonically increasing
        for i in range(len(aes_threads) - 1):
            assert aes_threads[i] <= aes_threads[i + 1], \
                f"AES threads not increasing: {aes_threads}"
    
    # ──────────────────────────────────────────────────────────────────────
    # SET/GET OPERATIONS
    # ──────────────────────────────────────────────────────────────────────
    
    def test_set_profile_all_valid(self):
        """Must be able to set any of the 5 profiles"""
        for profile_name in ['EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO',
                             'SERVER_GENERAL', 'DATACENTER_HIGH']:
            self.manager.set_profile(profile_name)
            assert self.manager.get_active_profile() == profile_name
    
    def test_set_profile_invalid(self):
        """Setting invalid profile must raise ValueError"""
        with pytest.raises(ValueError):
            self.manager.set_profile('INVALID_PROFILE')
    
    def test_get_profile_parameters(self):
        """Getting parameters must return all 8 required keys"""
        self.manager.set_profile('CLIENT_STANDARD')
        params = self.manager.get_profile_parameters()
        
        required_keys = {
            'chunk_size_bytes', 'compression_depth', 'pipeline_mode',
            'aes_batch_size', 'aes_threads', 'dp_window_seconds',
            'dp_epsilon_default', 'fallback_latency_threshold_ms'
        }
        
        assert required_keys.issubset(set(params.keys()))
    
    def test_get_profile_parameters_specific(self):
        """Can get parameters for specific profile without setting active"""
        params = self.manager.get_profile_parameters('SERVER_GENERAL')
        assert params['chunk_size_bytes'] == 512000
        assert params['compression_depth'] == 'HIGH'
    
    # ──────────────────────────────────────────────────────────────────────
    # AUTO SELECTION
    # ──────────────────────────────────────────────────────────────────────
    
    def test_auto_selection_determinism(self):
        """AUTO selection must be deterministic for same hardware"""
        hw = HardwareInfo.detect()
        
        # Run AUTO selection 10 times
        selections = []
        for _ in range(10):
            selection = self.manager.auto_select_profile(hw)
            selections.append(selection.profile_name)
        
        # All selections must be identical
        assert len(set(selections)) == 1, \
            f"AUTO selection not deterministic: {selections}"
    
    def test_auto_selection_returns_valid_profile(self):
        """AUTO selection must return one of the 5 profiles"""
        selection = self.manager.auto_select_profile()
        assert selection.profile_name in self.manager.profiles
    
    def test_auto_selection_includes_hardware_info(self):
        """AUTO selection must include hardware information"""
        selection = self.manager.auto_select_profile()
        assert selection.hardware_info is not None
        assert selection.hardware_info.cpu_cores > 0
        assert selection.hardware_info.total_memory_gb > 0
    
    def test_auto_selection_includes_justification(self):
        """AUTO selection must include human-readable justification"""
        selection = self.manager.auto_select_profile()
        assert len(selection.justification) > 0
        assert 'Selected' in selection.justification
    
    # ──────────────────────────────────────────────────────────────────────
    # FALLBACK MECHANISM
    # ──────────────────────────────────────────────────────────────────────
    
    def test_fallback_chain_complete(self):
        """All profiles must be in fallback chain"""
        chain = self.manager.spec['fallback_rules']['chain']
        
        for profile_name in self.manager.profiles.keys():
            assert profile_name in chain, f"{profile_name} not in fallback chain"
    
    def test_fallback_chain_valid_profiles(self):
        """Fallback chain must reference valid profiles"""
        chain = self.manager.spec['fallback_rules']['chain']
        
        for from_profile, to_profile in chain.items():
            assert from_profile in self.manager.profiles
            assert to_profile in self.manager.profiles
    
    def test_fallback_only_one_level(self):
        """Fallback must downgrade only ONE level"""
        chain = self.manager.spec['fallback_rules']['chain']
        
        profiles_ordered = [
            'EDGE_LOW',
            'CLIENT_STANDARD',
            'WORKSTATION_PRO',
            'SERVER_GENERAL',
            'DATACENTER_HIGH'
        ]
        
        for i, profile in enumerate(profiles_ordered[:-1]):
            # If fallback exists, should be to next profile
            if chain[profile] != profile:
                expected_next = profiles_ordered[i + 1]
                assert chain[profile] == expected_next, \
                    f"Fallback from {profile} should be {expected_next}, got {chain[profile]}"
    
    def test_fallback_from_highest(self):
        """DATACENTER_HIGH should fallback to SERVER_GENERAL"""
        chain = self.manager.spec['fallback_rules']['chain']
        assert chain['DATACENTER_HIGH'] == 'SERVER_GENERAL'
    
    def test_fallback_from_lowest(self):
        """EDGE_LOW cannot fallback (stays same)"""
        chain = self.manager.spec['fallback_rules']['chain']
        assert chain['EDGE_LOW'] == 'EDGE_LOW'
    
    def test_safe_fallback_operation(self):
        """Safe fallback must work correctly"""
        self.manager.set_profile('SERVER_GENERAL')
        
        # Fallback should succeed
        result = self.manager.safe_fallback("test latency", 350.0)
        assert result is True
        assert self.manager.get_active_profile() == 'WORKSTATION_PRO'
    
    def test_safe_fallback_history(self):
        """Fallback must be recorded in history"""
        self.manager.set_profile('SERVER_GENERAL')
        self.manager.safe_fallback("test reason", 100.0)
        
        history = self.manager.get_fallback_history()
        assert len(history) == 1
        assert history[0][0] == 'SERVER_GENERAL'
        assert history[0][1] == 'WORKSTATION_PRO'
        assert 'test reason' in history[0][2]
    
    # ──────────────────────────────────────────────────────────────────────
    # FFI INTERFACE COMPATIBILITY
    # ──────────────────────────────────────────────────────────────────────
    
    def test_ffi_set_profile(self):
        """FFI: set_profile() must work"""
        set_profile('WORKSTATION_PRO')
        # Reset to default
        set_profile('CLIENT_STANDARD')
    
    def test_ffi_auto_select(self):
        """FFI: auto_select_profile() must work"""
        profile = auto_select_profile()
        assert profile in self.manager.profiles
    
    def test_ffi_get_active(self):
        """FFI: get_active_profile() must work"""
        set_profile('SERVER_GENERAL')
        assert get_active_profile() == 'SERVER_GENERAL'
    
    def test_ffi_get_parameters(self):
        """FFI: get_profile_parameters() must work"""
        set_profile('DATACENTER_HIGH')
        params = get_profile_parameters()
        assert params['chunk_size_bytes'] == 1048576
    
    def test_ffi_explain(self):
        """FFI: explain_profile_selection() must work"""
        auto_select_profile()
        explanation = explain_profile_selection()
        assert len(explanation) > 0
    
    # ──────────────────────────────────────────────────────────────────────
    # DETERMINISM GUARANTEES
    # ──────────────────────────────────────────────────────────────────────
    
    def test_auto_determinism_across_instances(self):
        """AUTO selection must be deterministic across different manager instances"""
        hw = HardwareInfo.detect()
        
        manager1 = PerformanceProfileManager()
        selection1 = manager1.auto_select_profile(hw)
        
        manager2 = PerformanceProfileManager()
        selection2 = manager2.auto_select_profile(hw)
        
        assert selection1.profile_name == selection2.profile_name
    
    # ──────────────────────────────────────────────────────────────────────
    # IMMUTABILITY
    # ──────────────────────────────────────────────────────────────────────
    
    def test_profile_definitions_immutable(self):
        """Profile definitions must be immutable"""
        assert self.manager.spec['metadata']['immutable'] is True
        assert self.manager.spec['metadata']['version_locked'] is True
    
    def test_profiles_do_not_affect_format(self):
        """Spec must document what profiles do NOT affect"""
        do_not_affect = self.manager.spec['metadata']['what_profiles_do_not_affect']
        assert len(do_not_affect) > 0
        assert any('File format' in s or 'format' in s.lower() for s in do_not_affect)
        assert any('Decompression' in s or 'decompression' in s.lower() for s in do_not_affect)


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_get_active_profile_before_selection(self):
        """Getting active profile before selection must raise error"""
        manager = PerformanceProfileManager()
        with pytest.raises(RuntimeError):
            manager.get_active_profile()
    
    def test_get_parameters_before_selection(self):
        """Getting parameters before selection must raise error"""
        manager = PerformanceProfileManager()
        with pytest.raises(RuntimeError):
            manager.get_profile_parameters()
    
    def test_hardware_info_detection(self):
        """Hardware info detection must return valid values"""
        hw = HardwareInfo.detect()
        assert hw.cpu_cores >= 1
        assert hw.total_memory_gb >= 0.25  # At least 256 MB
    
    def test_profile_constraints_documented(self):
        """All profiles must document hardware constraints"""
        manager = PerformanceProfileManager()
        
        for profile in manager.profiles.values():
            assert profile.constraints is not None
            # At least one constraint defined
            assert len(profile.constraints) > 0


# ============================================================================
# Test Execution
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Performance Profile System - Comprehensive Test Suite")
    print("=" * 80)
    
    # Run with pytest if available
    try:
        pytest.main([__file__, "-v", "--tb=short"])
    except ImportError:
        print("\npytest not available. Running basic validation...")
        
        manager = PerformanceProfileManager()
        
        # Basic checks
        assert len(manager.profiles) == 5
        assert manager.validate_spec()
        assert manager.test_auto_determinism()
        assert manager.test_fallback_determinism()
        
        print("\n✓ Basic validation passed")
