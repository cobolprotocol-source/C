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
    # sign payload with orchestrator key to simulate authenticated sender
    import hmac, hashlib, binascii
    sig_msg = (payload['hash'] + '|' + str(payload['timestamp'])).encode()
    sig = hmac.new(binascii.unhexlify(orch.federation_key), sig_msg, hashlib.sha256).hexdigest()
    # pass signature timestamp via pattern_count tuple (pattern_count, sig_ts)
    res = fed.broadcast_dictionary(payload['hash'], mcdc_origin='nodeX', pattern_count=(payload['pattern_count'], payload['timestamp']), signature=sig)
    assert res.get('rejected') is True

    # second attempt: sender trims to orchestrator cap and retries
    trimmed = mgr.prepare_advertisement(orchestrator_cap=orch.federation_pattern_cap)
    sig_msg2 = (trimmed['hash'] + '|' + str(trimmed['timestamp'])).encode()
    sig2 = hmac.new(binascii.unhexlify(orch.federation_key), sig_msg2, hashlib.sha256).hexdigest()
    res2 = fed.broadcast_dictionary(trimmed['hash'], mcdc_origin='nodeX', pattern_count=(trimmed['pattern_count'], trimmed['timestamp']), signature=sig2)
    assert res2.get('rejected') is not True
    assert 'broadcast' in res2
