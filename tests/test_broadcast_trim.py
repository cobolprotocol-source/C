import os
import sys
import time

# ensure workspace root on path so modules can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from federated_dictionary_learning import (
    DistributedDictionaryManager, FederationStrategy
)
from cluster_orchestrator import MCDCOrchestrator, FederationProtocol


def test_broadcast_reject_and_trim():
    # setup manager with some patterns
    mgr = DistributedDictionaryManager(
        aggregation_strategy=FederationStrategy.FREQUENCY_WEIGHTED,
        global_cap=50
    )
    mgr.register_node('nodeX')

    # add many distinct patterns to force a larger global dictionary
    for i in range(40):
        mgr.update_local_dictionary('nodeX', bytes([i % 256]) * ((i % 8) + 2))
    mgr.federated_aggregation(use_privacy=False)

    # orchestrator with low cap to force rejection
    orch = MCDCOrchestrator(num_mcdc=3)
    orch.federation_pattern_cap = 1
    fed = FederationProtocol(orch)

    # first attempt: send actual pattern_count, expect rejection
    payload = mgr.prepare_advertisement()
    res = fed.broadcast_dictionary(payload['hash'], mcdc_origin='nodeX', pattern_count=payload['pattern_count'])
    assert res.get('rejected') is True

    # second attempt: sender trims to orchestrator cap and retries
    trimmed = mgr.prepare_advertisement(orchestrator_cap=orch.federation_pattern_cap)
    res2 = fed.broadcast_dictionary(trimmed['hash'], mcdc_origin='nodeX', pattern_count=trimmed['pattern_count'])
    assert res2.get('rejected') is not True
    assert 'broadcast' in res2
