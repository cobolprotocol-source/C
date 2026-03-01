import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from federated_dictionary_learning import DistributedDictionaryManager, FederationStrategy
from cluster_orchestrator import MCDCOrchestrator, FederationProtocol

import hmac, hashlib, binascii


def test_invalid_signature_rejected():
    mgr = DistributedDictionaryManager(aggregation_strategy=FederationStrategy.FREQUENCY_WEIGHTED)
    mgr.register_node('nodeY')
    mgr.update_local_dictionary('nodeY', b'ABCDEFG' * 10)
    mgr.federated_aggregation(use_privacy=False)

    orch = MCDCOrchestrator()
    fed = FederationProtocol(orch)

    payload = mgr.prepare_advertisement()
    # produce an invalid signature by flipping a bit
    sig_msg = (payload['hash'] + '|' + str(payload['timestamp'])).encode()
    valid = hmac.new(binascii.unhexlify(orch.federation_key), sig_msg, hashlib.sha256).hexdigest()
    invalid = ('0' if valid[0] != '0' else '1') + valid[1:]

    res = fed.broadcast_dictionary(payload['hash'], mcdc_origin='nodeY', pattern_count=(payload['pattern_count'], payload['timestamp']), signature=invalid)
    assert res.get('rejected') is True


def test_replay_detection():
    mgr = DistributedDictionaryManager(aggregation_strategy=FederationStrategy.FREQUENCY_WEIGHTED)
    mgr.register_node('nodeZ')
    mgr.update_local_dictionary('nodeZ', b'XYZ' * 20)
    mgr.federated_aggregation(use_privacy=False)

    orch = MCDCOrchestrator()
    fed = FederationProtocol(orch)

    payload = mgr.prepare_advertisement()
    sig_msg = (payload['hash'] + '|' + str(payload['timestamp'])).encode()
    sig = hmac.new(binascii.unhexlify(orch.federation_key), sig_msg, hashlib.sha256).hexdigest()

    # first broadcast should succeed
    res1 = fed.broadcast_dictionary(payload['hash'], mcdc_origin='nodeZ', pattern_count=(payload['pattern_count'], payload['timestamp']), signature=sig)
    assert 'broadcast' in res1

    # immediate re-broadcast with same timestamp/signature should be detected as replay
    res2 = fed.broadcast_dictionary(payload['hash'], mcdc_origin='nodeZ', pattern_count=(payload['pattern_count'], payload['timestamp']), signature=sig)
    assert res2.get('rejected') is True
    assert res2.get('reason') == 'replay_detected'
