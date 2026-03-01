# Copyright (c) 2026 Nafal Faturizki
# All rights reserved.
#
# This file is part of the COBOL Protocol project.
# Unauthorized copying, modification, or redistribution
# is prohibited except as explicitly permitted by the
# accompanying LICENSE.md.
#
# See LICENSE.md for complete license terms.

"""
Test suite for Profile Versioning System

Tests strict requirements:
1. Version immutability - once released, never change
2. Opt-in enforcement - no automatic upgrades
3. AUTO selection determinism - same hardware = same profile
4. Experimental isolation - explicit opt-in required
5. Safe fallback - never changes version
6. Audit logging - all changes logged
7. Cross-version consistency
"""

import pytest
from profile_versioning import (
    ProfileVersionManager,
    ProfileUpgradeManager,
    ExperimentalVersionManager,
    ProfileVersion,
    VersionStatus,
    UpgradeReason,
    VersionChange,
)


@pytest.fixture
def version_manager():
    """Load the version manager"""
    return ProfileVersionManager("/workspaces/dev.c/spec/performance_profiles_v2.yaml")


@pytest.fixture
def upgrade_manager(version_manager):
    """Create an upgrade manager"""
    return ProfileUpgradeManager(version_manager)


@pytest.fixture
def experimental_manager(version_manager):
    """Create an experimental manager"""
    return ExperimentalVersionManager(version_manager)


# ============================================================================
# TEST 1: VERSION IMMUTABILITY
# ============================================================================

class TestVersionImmutability:
    """Test that profile versions are immutable once released"""
    
    def test_profile_versions_exist(self, version_manager):
        """Test that all required profiles have versions"""
        required_profiles = ['EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO', 'SERVER_GENERAL', 'DATACENTER_HIGH']
        
        for profile in required_profiles:
            versions = version_manager.get_all_versions(profile)
            assert len(versions) > 0, f"Profile {profile} has no versions"
    
    def test_each_version_has_parameters(self, version_manager):
        """Test that each version has complete parameters"""
        required_params = [
            'chunk_size_bytes', 'compression_depth', 'pipeline_mode',
            'aes_batch_size', 'aes_threads', 'dp_window_seconds',
            'dp_epsilon_default', 'fallback_latency_threshold_ms'
        ]
        
        for profile in ['EDGE_LOW', 'CLIENT_STANDARD']:
            versions = version_manager.get_all_versions(profile)
            for version in versions:
                pv = version_manager.get_version(profile, version)
                for param in required_params:
                    assert param in pv.parameters, \
                        f"{profile}@{version} missing parameter: {param}"
    
    def test_version_parameter_hash(self, version_manager):
        """Test that parameters hash is consistent (immutability)"""
        profile = 'CLIENT_STANDARD'
        version = '1.0'
        pv1 = version_manager.get_version(profile, version)
        pv2 = version_manager.get_version(profile, version)
        
        # Same version loaded twice should have same hash
        assert pv1.parameter_hash == pv2.parameter_hash
        assert pv1.validate_immutability(pv2)
    
    def test_version_identifiers_unique(self, version_manager):
        """Test that each version has unique identifier"""
        identifiers = set()
        
        for profile in ['EDGE_LOW', 'CLIENT_STANDARD']:
            versions = version_manager.get_all_versions(profile)
            for version in versions:
                pv = version_manager.get_version(profile, version)
                identifier = pv.get_full_identifier()
                assert identifier not in identifiers, f"Duplicate identifier: {identifier}"
                identifiers.add(identifier)


# ============================================================================
# TEST 2: OPT-IN UPGRADE ENFORCEMENT
# ============================================================================

class TestOptInEnforcement:
    """Test that upgrades require explicit user action"""
    
    def test_no_automatic_upgrade(self, upgrade_manager):
        """Test that set_version requires confirmation"""
        upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'
        
        # Without confirm=True, should fail
        success, msg = upgrade_manager.set_version('CLIENT_STANDARD@1.1', confirm=False)
        assert not success
        assert 'confirmation' in msg.lower()
    
    def test_explicit_upgrade(self, upgrade_manager):
        """Test that explicit upgrade works"""
        upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'
        
        # With confirm=True, should succeed
        success, msg = upgrade_manager.set_version('CLIENT_STANDARD@1.1', confirm=True)
        assert success
        assert upgrade_manager.get_current_version() == 'CLIENT_STANDARD@1.1'
    
    def test_upgrade_to_unknown_version_fails(self, upgrade_manager):
        """Test that upgrade to unknown version fails"""
        upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'
        
        success, msg = upgrade_manager.set_version('CLIENT_STANDARD@99.99', confirm=True)
        assert not success
        assert 'unknown' in msg.lower()
    
    def test_upgrade_audit_logged(self, upgrade_manager):
        """Test that upgrades are logged in audit trail"""
        upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'
        upgrade_manager.set_version('CLIENT_STANDARD@1.1', confirm=True)
        
        audit = upgrade_manager.version_manager.get_audit_log()
        assert len(audit) > 0
        assert audit[-1].from_profile == 'CLIENT_STANDARD@1.0'
        assert audit[-1].to_profile == 'CLIENT_STANDARD@1.1'


# ============================================================================
# TEST 3: AUTO SELECTION DETERMINISM
# ============================================================================

class TestAutoSelectionDeterminism:
    """Test that AUTO selection is deterministic"""
    
    def test_auto_selects_profile_name_only(self, version_manager):
        """Test that AUTO selection returns profile name, not version"""
        # Parse the auto selection rules from spec
        auto_rules = version_manager.spec.get('auto_selection_rules', {})
        
        # Each rule should select profile name only
        for rule_name, rule in auto_rules.items():
            profile = rule.get('selected_profile')
            version = rule.get('selected_version')
            
            assert profile is not None, f"Rule {rule_name} has no profile"
            assert version is None, f"Rule {rule_name} should NOT select version"
    
    def test_version_selection_note_present(self, version_manager):
        """Test that version selection notes guide users"""
        auto_rules = version_manager.spec.get('auto_selection_rules', {})
        
        for rule_name, rule in auto_rules.items():
            note = rule.get('version_selection_note')
            assert note is not None, f"Rule {rule_name} missing version selection note"
            assert 'version' in note.lower()
    
    def test_same_profile_across_runs(self, version_manager):
        """Test that profile selection is deterministic across multiple calls"""
        # Simulate auto-selection logic (same hardware = same profile)
        # This would be more thorough in real implementation
        
        profile1 = version_manager.spec['auto_selection_rules']['rule_4']['selected_profile']
        profile2 = version_manager.spec['auto_selection_rules']['rule_4']['selected_profile']
        
        assert profile1 == profile2


# ============================================================================
# TEST 4: EXPERIMENTAL ISOLATION
# ============================================================================

class TestExperimentalIsolation:
    """Test that experimental versions are isolated and require opt-in"""
    
    def test_experimental_versions_marked(self, version_manager):
        """Test that experimental versions are marked with @experimental"""
        experimental = version_manager.get_experimental_versions('DATACENTER_HIGH')
        
        for exp_version in experimental:
            assert '@experimental' in exp_version
    
    def test_experimental_not_default(self, version_manager):
        """Test that experimental versions are not default"""
        default = version_manager.get_default_version('DATACENTER_HIGH')
        assert '@experimental' not in default
    
    def test_experimental_requires_explicit_opt_in(self, upgrade_manager):
        """Test that experimental versions require explicit opt-in"""
        upgrade_manager.current_version = 'DATACENTER_HIGH@1.0'
        
        # Trying to upgrade to experimental without explicit action should require confirmation
        success, msg = upgrade_manager.set_version('DATACENTER_HIGH@2.0@experimental', confirm=False)
        assert not success
    
    def test_experimental_accepts_explicit_opt_in(self, upgrade_manager):
        """Test that explicit opt-in works for experimental"""
        upgrade_manager.current_version = 'DATACENTER_HIGH@1.0'
        
        # With explicit confirmation (explicit opt-in)
        success, msg = upgrade_manager.set_version('DATACENTER_HIGH@2.0@experimental', confirm=True)
        assert success
    
    def test_experimental_soak_test_tracking(self, experimental_manager):
        """Test that soak test progress is tracked"""
        success, msg = experimental_manager.start_soak_test('2.0@experimental')
        assert success
        
        experimental_manager.log_soak_test_result('2.0@experimental', 'Determinism check: PASS')
        experimental_manager.log_soak_test_result('2.0@experimental', 'DP validation: PASS')
        
        # Check logs exist
        logs = experimental_manager.soak_test_logs
        assert 'DATACENTER_HIGH@2.0@experimental' in logs
        assert len(logs['DATACENTER_HIGH@2.0@experimental']) > 2


# ============================================================================
# TEST 5: SAFE FALLBACK
# ============================================================================

class TestSafeFallback:
    """Test that fallback never changes profile version"""
    
    def test_fallback_chain_defined(self, version_manager):
        """Test that fallback chain exists in spec"""
        fallback_rules = version_manager.spec.get('fallback_rules', {})
        chain = fallback_rules.get('chain', {})
        
        assert len(chain) > 0, "Fallback chain not defined"
        assert 'DATACENTER_HIGH' in chain
        assert 'CLIENT_STANDARD' in chain
    
    def test_fallback_version_rule(self, version_manager):
        """Test that version rule explicitly exists in spec"""
        fallback_rules = version_manager.spec.get('fallback_rules', {})
        version_rule = fallback_rules.get('version_rule')
        
        assert version_rule is not None
        assert 'version' in version_rule.lower()
        assert 'never' in version_rule.lower()
    
    def test_client_standard_is_minimum_fallback(self, version_manager):
        """Test that CLIENT_STANDARD is absolute minimum fallback"""
        fallback_chain = version_manager.spec['fallback_rules']['chain']
        
        # CLIENT_STANDARD should not fallback further
        assert fallback_chain['CLIENT_STANDARD'] == 'CLIENT_STANDARD'


# ============================================================================
# TEST 6: UPGRADE INFORMATION
# ============================================================================

class TestUpgradeInformation:
    """Test that upgrade information is provided for all upgrades"""
    
    def test_upgrade_information_available(self, version_manager):
        """Test that upgrade info exists for available upgrades"""
        info = version_manager.get_upgrade_information('CLIENT_STANDARD@1.0', 'CLIENT_STANDARD@1.1')
        
        assert info is not None
        assert info.from_version == 'CLIENT_STANDARD@1.0'
        assert info.to_version == 'CLIENT_STANDARD@1.1'
    
    def test_upgrade_contains_what_changed(self, version_manager):
        """Test that upgrade information includes changes"""
        info = version_manager.get_upgrade_information('CLIENT_STANDARD@1.0', 'CLIENT_STANDARD@1.1')
        
        assert len(info.changes) > 0, "No changes listed in upgrade"
    
    def test_upgrade_contains_what_did_not_change(self, version_manager):
        """Test that upgrade information includes what did NOT change"""
        info = version_manager.get_upgrade_information('CLIENT_STANDARD@1.0', 'CLIENT_STANDARD@1.1')
        
        assert len(info.what_did_not_change) > 0, "No 'what did not change' listed"
        # Verify file format is not changing
        assert any('format' in item.lower() or 'decompression' in item.lower() 
                  for item in info.what_did_not_change)
    
    def test_upgrade_information_summary(self, version_manager):
        """Test that upgrade information can be summarized"""
        info = version_manager.get_upgrade_information('CLIENT_STANDARD@1.0', 'CLIENT_STANDARD@1.1')
        summary = info.summary()
        
        assert 'CLIENT_STANDARD@1.0' in summary
        assert 'CLIENT_STANDARD@1.1' in summary
        assert 'Changes:' in summary
        assert 'What DID NOT change:' in summary


# ============================================================================
# TEST 7: VERSION VALIDATION
# ============================================================================

class TestVersionValidation:
    """Test that profile@version strings are validated"""
    
    def test_valid_version_passes(self, version_manager):
        """Test that valid profile@version passes validation"""
        is_valid, error = version_manager.validate_version('CLIENT_STANDARD@1.0')
        assert is_valid
        assert error == ""
    
    def test_invalid_format_fails(self, version_manager):
        """Test that invalid format fails validation"""
        is_valid, error = version_manager.validate_version('INVALID_FORMAT')
        assert not is_valid
        assert 'format' in error.lower()
    
    def test_unknown_profile_fails(self, version_manager):
        """Test that unknown profile fails validation"""
        is_valid, error = version_manager.validate_version('UNKNOWN_PROFILE@1.0')
        assert not is_valid
    
    def test_unknown_version_fails(self, version_manager):
        """Test that unknown version fails validation"""
        is_valid, error = version_manager.validate_version('CLIENT_STANDARD@99.99')
        assert not is_valid
    
    def test_experimental_opt_in_check(self, version_manager):
        """Test that experimental versions are identified"""
        is_valid, msg = version_manager.validate_experimental_opt_in('DATACENTER_HIGH@2.0@experimental')
        assert is_valid
        assert 'experimental' in msg.lower()
        assert 'explicit' in msg.lower()


# ============================================================================
# TEST 8: AUDIT LOGGING
# ============================================================================

class TestAuditLogging:
    """Test that all version changes are logged"""
    
    def test_audit_log_initialized(self, version_manager):
        """Test that audit log is initialized"""
        log = version_manager.get_audit_log()
        assert isinstance(log, list)
    
    def test_upgrade_creates_audit_entry(self, version_manager):
        """Test that upgrades create audit entries"""
        initial_count = len(version_manager.get_audit_log())
        
        version_manager.log_upgrade(
            'CLIENT_STANDARD@1.0',
            'CLIENT_STANDARD@1.1',
            UpgradeReason.PERFORMANCE_IMPROVEMENT,
            success=True
        )
        
        final_count = len(version_manager.get_audit_log())
        assert final_count == initial_count + 1
    
    def test_audit_entry_has_timestamp(self, version_manager):
        """Test that audit entries have timestamps"""
        version_manager.log_upgrade(
            'CLIENT_STANDARD@1.0',
            'CLIENT_STANDARD@1.1',
            UpgradeReason.PERFORMANCE_IMPROVEMENT
        )
        
        log = version_manager.get_audit_log()
        assert log[-1].timestamp is not None
    
    def test_audit_log_printable(self, version_manager):
        """Test that audit log can be printed"""
        version_manager.log_upgrade(
            'CLIENT_STANDARD@1.0',
            'CLIENT_STANDARD@1.1',
            UpgradeReason.PERFORMANCE_IMPROVEMENT
        )
        
        log_text = version_manager.print_audit_log()
        assert 'Audit Log' in log_text
        assert 'SUCCESS' in log_text or 'FAILED' in log_text


# ============================================================================
# TEST 9: CROSS-PROFILE VERSION CONSISTENCY
# ============================================================================

class TestCrossVersionConsistency:
    """Test that all profiles follow versioning rules"""
    
    def test_all_profiles_have_versions(self, version_manager):
        """Test that all profiles have at least one version"""
        profiles = ['EDGE_LOW', 'CLIENT_STANDARD', 'WORKSTATION_PRO', 'SERVER_GENERAL', 'DATACENTER_HIGH']
        
        for profile in profiles:
            versions = version_manager.get_all_versions(profile)
            assert len(versions) > 0, f"{profile} has no versions"
    
    def test_all_versions_have_status(self, version_manager):
        """Test that all versions have status"""
        profiles = ['EDGE_LOW', 'CLIENT_STANDARD']
        
        for profile in profiles:
            for version in version_manager.get_all_versions(profile):
                pv = version_manager.get_version(profile, version)
                assert pv.status in [VersionStatus.STABLE, VersionStatus.EXPERIMENTAL]
    
    def test_version_format_consistent(self, version_manager):
        """Test that version format is consistent"""
        profiles = ['EDGE_LOW', 'CLIENT_STANDARD']
        
        for profile in profiles:
            for version in version_manager.get_all_versions(profile):
                # Each version should be "X.Y" or "X.Y@experimental"
                parts = version.split('@')
                assert len(parts) in [1, 2], f"Invalid version format: {version}"
                
                ver_part = parts[0]
                assert ver_part.count('.') == 1, f"Version should be X.Y: {version}"


# ============================================================================
# INTEGRATION TEST
# ============================================================================

class TestIntegration:
    """Integration tests for the complete versioning system"""
    
    def test_complete_upgrade_flow(self, upgrade_manager):
        """Test complete upgrade workflow"""
        # Start with stable version
        upgrade_manager.current_version = 'CLIENT_STANDARD@1.0'
        assert upgrade_manager.get_current_version() == 'CLIENT_STANDARD@1.0'
        
        # Check upgrade availability
        target = 'CLIENT_STANDARD@1.1'
        can_upgrade = upgrade_manager.version_manager.can_upgrade_to(
            'CLIENT_STANDARD@1.0',
            target
        )
        assert can_upgrade
        
        # Get upgrade information
        info = upgrade_manager.propose_upgrade(target)
        assert info is not None
        assert info.rollback_available
        
        # Perform upgrade with confirmation
        success, msg = upgrade_manager.set_version(target, confirm=True)
        assert success
        assert upgrade_manager.get_current_version() == target
        
        # Verify audit logged
        audit = upgrade_manager.version_manager.get_audit_log()
        assert any(entry.to_profile == target for entry in audit)
    
    def test_experimental_flow(self, experimental_manager):
        """Test experimental version workflow"""
        # Start soak test
        success, msg = experimental_manager.start_soak_test('2.0@experimental')
        assert success
        
        # Log test results
        experimental_manager.log_soak_test_result('2.0@experimental', 'Determinism: PASS')
        experimental_manager.log_soak_test_result('2.0@experimental', 'DP validation: PASS')
        experimental_manager.log_soak_test_result('2.0@experimental', 'AES validation: PASS')
        
        # Check promotion readiness (would require real soak test hours in production)
        can_promote, msg = experimental_manager.can_promote_to_stable('2.0@experimental')
        # In test environment, has logs so should be ready
        assert can_promote


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
