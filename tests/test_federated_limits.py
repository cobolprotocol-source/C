import os
import sys
import time
import pytest

# ensure workspace root on path so modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from federated_dictionary_learning import (
    DistributedDictionaryManager, LocalDictionary, PatternInfo)
from federated_dictionary_learning import FederationStrategy


def make_pattern(i: int) -> bytes:
    return bytes([i % 256]) * ((i % 8) + 1)


def test_global_cap_and_cost_and_ttl():
    mgr = DistributedDictionaryManager(
        aggregation_strategy=FederationStrategy.FREQUENCY_WEIGHTED,
        global_cap=10,          # small cap for test
        entropy_threshold=0.0,
        cost_max=5,             # patterns with high cost removed
        ttl_hours=0.001         # expire quickly
    )

    # register a single node and populate with many patterns
    mgr.register_node('nodeA')
    data = b''.join(make_pattern(i) for i in range(20))
    mgr.update_local_dictionary('nodeA', data)

    # perform aggregation
    global_dict = mgr.federated_aggregation(use_privacy=False)

    # check cap enforced
    assert len(global_dict) <= 10

    # check cost filter (all patterns should have cost <= 5)
    for info in global_dict.values():
        assert mgr._pattern_cost(info) <= 5

    # wait for TTL expiry and re-aggregate
    time.sleep(5)  # TTL 0.001 hr ~3.6s, so sleep longer to ensure expiration
    global_dict2 = mgr.federated_aggregation(use_privacy=False)
    assert len(global_dict2) == 0


def test_entropy_threshold():
    mgr = DistributedDictionaryManager(
        aggregation_strategy=FederationStrategy.ENTROPY_BASED,
        global_cap=100,
        entropy_threshold=0.5,
    )
    mgr.register_node('nodeB')
    # create patterns with same frequency so entropy contributions equal
    for _ in range(10):
        mgr.update_local_dictionary('nodeB', b'AB')
    # calculate entropy manually: should be high enough
    mgr.local_dictionaries['nodeB'].calculate_entropy()
    global_dict = mgr.federated_aggregation(use_privacy=False)
    # all patterns in resulting dict should have entropy >= threshold
    for info in global_dict.values():
        assert info.entropy >= 0.5
