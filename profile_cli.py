#!/usr/bin/env python3
"""
Performance Profile System - Command-line Interface

Usage:
  python3 profile_cli.py                    # Show current profile
  python3 profile_cli.py auto               # Auto-select profile
  python3 profile_cli.py set SERVER_GENERAL # Set specific profile
  python3 profile_cli.py explain            # Explain selection
  python3 profile_cli.py list               # List all profiles
  python3 profile_cli.py info <profile>     # Show profile details
  python3 profile_cli.py test               # Run tests
"""

import sys
import argparse
from performance_profiles import (
    PerformanceProfileManager,
    HardwareInfo,
    set_profile,
    auto_select_profile,
    get_active_profile,
    get_profile_parameters,
    explain_profile_selection,
    get_manager,
)


def print_header(title):
    """Print a formatted header"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def cmd_current():
    """Show current active profile"""
    manager = get_manager()
    try:
        active = manager.get_active_profile()
        params = manager.get_profile_parameters()
        
        print_header(f"Current Profile: {active}")
        print(f"Profile: {active}")
        print(f"Chunk size: {params['chunk_size_bytes']:,} bytes")
        print(f"Compression depth: {params['compression_depth']}")
        print(f"Pipeline mode: {params['pipeline_mode']}")
        print(f"AES threads: {params['aes_threads']}")
        print(f"DP window: {params['dp_window_seconds']}s")
        print(f"Fallback threshold: {params['fallback_latency_threshold_ms']}ms")
        
    except RuntimeError:
        print_header("No Profile Selected")
        print("❌ No profile has been selected yet.")
        print("   Use: python3 profile_cli.py auto")
        sys.exit(1)


def cmd_auto():
    """Auto-select profile based on hardware"""
    manager = get_manager()
    profile_name = auto_select_profile()  # FFI returns string, not ProfileSelection
    selection = manager.auto_select_profile()  # Get full selection from manager
    
    print_header(f"Auto-Selected Profile: {profile_name}")
    print(f"✓ Selected: {profile_name}")
    print(f"✓ Hardware detected:")
    print(f"    Cores: {selection.hardware_info.cpu_cores}")
    print(f"    RAM: {selection.hardware_info.total_memory_gb:.1f} GB")
    print(f"    AES-NI: {selection.hardware_info.aes_ni_available}")
    if selection.hardware_info.numa_present is not None:
        print(f"    NUMA: {selection.hardware_info.numa_present}")
    print(f"\n✓ Reason: {selection.justification}")
    print()


def cmd_set(profile_name):
    """Set a specific profile"""
    manager = get_manager()
    
    if profile_name not in manager.profiles:
        print_header("Invalid Profile")
        print(f"❌ Unknown profile: {profile_name}")
        print(f"   Valid profiles: {', '.join(manager.profiles.keys())}")
        sys.exit(1)
    
    manager.set_profile(profile_name)
    print_header(f"Profile Set: {profile_name}")
    print(f"✓ Profile set to: {profile_name}")
    
    params = manager.get_profile_parameters()
    print(f"\nProfile parameters:")
    print(f"  chunk_size_bytes: {params['chunk_size_bytes']:,}")
    print(f"  compression_depth: {params['compression_depth']}")
    print(f"  pipeline_mode: {params['pipeline_mode']}")
    print(f"  aes_threads: {params['aes_threads']}")
    print(f"  dp_window_seconds: {params['dp_window_seconds']}")
    print()


def cmd_explain():
    """Explain current profile selection"""
    manager = get_manager()
    
    try:
        explanation = manager.explain_profile_selection()
        print_header("Profile Selection Explanation")
        print(f"Current profile: {manager.get_active_profile()}")
        print(f"Explanation: {explanation}")
        print()
    except RuntimeError:
        print_header("No Profile Selected")
        print("❌ No profile has been selected yet.")
        print("   Use: python3 profile_cli.py auto")
        sys.exit(1)


def cmd_list():
    """List all available profiles"""
    manager = PerformanceProfileManager()
    
    print_header("Available Profiles")
    
    profiles = [
        ('EDGE_LOW', '1-2 cores', '<2 GB', '8 KB', 'IoT, edge devices'),
        ('CLIENT_STANDARD', '2-8 cores', '4-32 GB', '64 KB', 'Laptops, desktops (SAFE FALLBACK)'),
        ('WORKSTATION_PRO', '8-16 cores', '32+ GB', '256 KB', 'Workstations'),
        ('SERVER_GENERAL', '16-64 cores', '64+ GB', '512 KB', 'Enterprise servers'),
        ('DATACENTER_HIGH', '64+ cores', '256+ GB', '1 MB', 'HPC, large-scale'),
    ]
    
    print(f"{'Profile':<20} {'Cores':<15} {'RAM':<12} {'Chunk':<10} {'Use Case':<35}")
    print("-" * 92)
    
    for profile_name, cores, ram, chunk, use_case in profiles:
        if profile_name == 'CLIENT_STANDARD':
            marker = "⭐"
        else:
            marker = "  "
        print(f"{marker} {profile_name:<18} {cores:<15} {ram:<12} {chunk:<10} {use_case:<35}")
    
    print("\n⭐ = SAFE FALLBACK profile (minimum stable profile)")
    print()


def cmd_info(profile_name):
    """Show detailed information about a profile"""
    manager = PerformanceProfileManager()
    
    if profile_name not in manager.profiles:
        print_header("Invalid Profile")
        print(f"❌ Unknown profile: {profile_name}")
        print(f"   Valid profiles: {', '.join(manager.profiles.keys())}")
        sys.exit(1)
    
    profile = manager.profiles[profile_name]
    
    print_header(f"Profile Details: {profile_name}")
    
    print(f"Name: {profile.name}")
    print(f"Description: {profile.description}")
    print(f"Notes: {profile.notes}\n")
    
    print(f"Constraints:")
    for key, value in profile.constraints.items():
        print(f"  {key}: {value}")
    
    print(f"\nParameters:")
    print(f"  chunk_size_bytes: {profile.parameters.chunk_size_bytes:,}")
    print(f"  compression_depth: {profile.parameters.compression_depth}")
    print(f"  pipeline_mode: {profile.parameters.pipeline_mode}")
    print(f"  aes_batch_size: {profile.parameters.aes_batch_size}")
    print(f"  aes_threads: {profile.parameters.aes_threads}")
    print(f"  dp_window_seconds: {profile.parameters.dp_window_seconds}")
    print(f"  dp_epsilon_default: {profile.parameters.dp_epsilon_default}")
    print(f"  fallback_latency_threshold_ms: {profile.parameters.fallback_latency_threshold_ms}")
    
    print(f"\nCharacteristics:")
    for key, value in profile.characteristics.items():
        if isinstance(value, list):
            print(f"  {key}: {', '.join(value)}")
        else:
            print(f"  {key}: {value}")
    
    print()


def cmd_compare():
    """Compare all profiles side-by-side"""
    manager = PerformanceProfileManager()
    
    print_header("Profile Comparison")
    
    profiles = list(manager.profiles.values())
    
    # Chunk sizes
    print("Chunk Size Progression:")
    print("-" * 50)
    for profile in profiles:
        chunk_size = profile.parameters.chunk_size_bytes
        label = "⭐ " if profile.name == 'CLIENT_STANDARD' else "   "
        bar_length = int(chunk_size / 100000)  # Scale for visualization
        bar = "█" * min(bar_length, 50)
        print(f"{label}{profile.name:<20} {chunk_size:>8,} bytes {bar}")
    
    # AES threads
    print("\nAES Thread Utilization:")
    print("-" * 50)
    for profile in profiles:
        aes_threads = profile.parameters.aes_threads
        bar = "█" * aes_threads
        print(f"{profile.name:<20} {aes_threads:>2} threads {bar}")
    
    # Throughput
    print("\nEstimated Throughput:")
    print("-" * 50)
    throughputs = {
        'EDGE_LOW': 10,
        'CLIENT_STANDARD': 50,
        'WORKSTATION_PRO': 150,
        'SERVER_GENERAL': 300,
        'DATACENTER_HIGH': 500,
    }
    for profile_name, throughput in throughputs.items():
        label = "⭐ " if profile_name == 'CLIENT_STANDARD' else "   "
        bar = "▁" * (throughput // 50)
        print(f"{label}{profile_name:<20} ~{throughput:>3} MB/s {bar}")
    
    print()


def cmd_test():
    """Run validation tests"""
    manager = PerformanceProfileManager()
    
    print_header("Performance Profile System - Validation Tests")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Exactly 5 profiles
    tests_total += 1
    print("[1] Verify exactly 5 profiles...")
    if len(manager.profiles) == 5:
        print("    ✓ PASS\n")
        tests_passed += 1
    else:
        print(f"    ✗ FAIL: Expected 5 profiles, got {len(manager.profiles)}\n")
    
    # Test 2: Spec validation
    tests_total += 1
    print("[2] Validate specification...")
    if manager.validate_spec():
        print("    ✓ PASS\n")
        tests_passed += 1
    else:
        print("    ✗ FAIL: Spec validation failed\n")
    
    # Test 3: AUTO selection
    tests_total += 1
    print("[3] Test AUTO selection...")
    hw = HardwareInfo.detect()
    selection = manager.auto_select_profile(hw)
    if selection.profile_name in manager.profiles:
        print(f"    ✓ PASS: Selected {selection.profile_name}\n")
        tests_passed += 1
    else:
        print(f"    ✗ FAIL: Invalid profile selected\n")
    
    # Test 4: AUTO determinism
    tests_total += 1
    print("[4] Test AUTO selection determinism (10 iterations)...")
    selections = []
    for _ in range(10):
        sel = manager.auto_select_profile(hw)
        selections.append(sel.profile_name)
    if len(set(selections)) == 1:
        print(f"    ✓ PASS: All 10 iterations selected {selections[0]}\n")
        tests_passed += 1
    else:
        print(f"    ✗ FAIL: Selections not consistent: {set(selections)}\n")
    
    # Test 5: Fallback chain
    tests_total += 1
    print("[5] Validate fallback chain...")
    chain = manager.spec['fallback_rules']['chain']
    valid = (
        chain['DATACENTER_HIGH'] == 'SERVER_GENERAL' and
        chain['SERVER_GENERAL'] == 'WORKSTATION_PRO' and
        chain['WORKSTATION_PRO'] == 'CLIENT_STANDARD' and
        chain['CLIENT_STANDARD'] == 'CLIENT_STANDARD' and
        chain['EDGE_LOW'] == 'EDGE_LOW'
    )
    if valid:
        print("    ✓ PASS\n")
        tests_passed += 1
    else:
        print("    ✗ FAIL: Fallback chain invalid\n")
    
    # Test 6: Get/Set operations
    tests_total += 1
    print("[6] Test set/get profile operations...")
    try:
        manager.set_profile('SERVER_GENERAL')
        if manager.get_active_profile() == 'SERVER_GENERAL':
            print("    ✓ PASS\n")
            tests_passed += 1
        else:
            print("    ✗ FAIL: Profile not set correctly\n")
    except Exception as e:
        print(f"    ✗ FAIL: {e}\n")
    
    # Test 7: Parameters
    tests_total += 1
    print("[7] Test profile parameters...")
    manager.set_profile('WORKSTATION_PRO')
    params = manager.get_profile_parameters()
    required = {
        'chunk_size_bytes', 'compression_depth', 'pipeline_mode',
        'aes_batch_size', 'aes_threads', 'dp_window_seconds',
        'dp_epsilon_default', 'fallback_latency_threshold_ms'
    }
    if required.issubset(set(params.keys())):
        print(f"    ✓ PASS: All 8 parameters present\n")
        tests_passed += 1
    else:
        print(f"    ✗ FAIL: Missing parameters\n")
    
    # Summary
    print("=" * 80)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    if tests_passed == tests_total:
        print("✓ ALL TESTS PASSED")
    else:
        print(f"✗ {tests_total - tests_passed} test(s) failed")
    print("=" * 80)
    print()
    
    return 0 if tests_passed == tests_total else 1


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Performance Profile System - Command-line Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 profile_cli.py                # Show current profile
  python3 profile_cli.py auto           # Auto-select profile
  python3 profile_cli.py set WORKSTATION_PRO  # Set specific profile
  python3 profile_cli.py list           # List all profiles
  python3 profile_cli.py info SERVER_GENERAL  # Show profile details
  python3 profile_cli.py compare        # Compare all profiles
  python3 profile_cli.py explain        # Explain selection
  python3 profile_cli.py test           # Run validation tests
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Auto-select
    subparsers.add_parser('auto', help='Auto-select profile based on hardware')
    
    # Set profile
    set_parser = subparsers.add_parser('set', help='Set a specific profile')
    set_parser.add_argument('profile', help='Profile name')
    
    # Explain
    subparsers.add_parser('explain', help='Explain current profile selection')
    
    # List profiles
    subparsers.add_parser('list', help='List all available profiles')
    
    # Profile info
    info_parser = subparsers.add_parser('info', help='Show profile details')
    info_parser.add_argument('profile', help='Profile name')
    
    # Compare profiles
    subparsers.add_parser('compare', help='Compare all profiles')
    
    # Run tests
    subparsers.add_parser('test', help='Run validation tests')
    
    args = parser.parse_args()
    
    if args.command is None or args.command == 'set' and not hasattr(args, 'profile'):
        # No command or incomplete command
        if len(sys.argv) == 1:
            # No arguments - show current profile
            cmd_current()
        else:
            parser.print_help()
            sys.exit(1)
    elif args.command == 'auto':
        cmd_auto()
    elif args.command == 'set':
        cmd_set(args.profile)
    elif args.command == 'explain':
        cmd_explain()
    elif args.command == 'list':
        cmd_list()
    elif args.command == 'info':
        cmd_info(args.profile)
    elif args.command == 'compare':
        cmd_compare()
    elif args.command == 'test':
        return cmd_test()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
