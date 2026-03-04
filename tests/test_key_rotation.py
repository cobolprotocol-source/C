import os, sys, hmac, hashlib, binascii
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.layers.dictionaries.federated_dictionary_learning import DistributedDictionaryManager, FederationStrategy
from src.cluster_orchestrator import MCDCOrchestrator, FederationProtocol


def sign_payload(payload, key):
    msg = (payload['hash'] + '|' + str(payload['timestamp'])).encode()
    return hmac.new(binascii.unhexlify(key), msg, hashlib.sha256).hexdigest()


def test_key_rotation_allows_old_and_new():
    mgr = DistributedDictionaryManager(aggregation_strategy=FederationStrategy.FREQUENCY_WEIGHTED)
    mgr.register_node('nodeK')
    mgr.update_local_dictionary('nodeK', b'DATA' * 5)
    mgr.federated_aggregation(use_privacy=False)

    orch = MCDCOrchestrator()
    fed = FederationProtocol(orch)

    payload = mgr.prepare_advertisement()
    sig1 = sign_payload(payload, orch.federation_key)
    # broadcast with original key should succeed
    res1 = fed.broadcast_dictionary(payload['hash'], 'nodeK', pattern_count=(payload['pattern_count'], payload['timestamp']), signature=sig1)
    assert 'broadcast' in res1

    # rotate key, keep old
    # capture existing oldest key so we can verify it's retained
    oldkey = orch.active_federation_keys[0]
    newkey = orch.rotate_federation_key(keep_old=1)
    assert newkey in orch.active_federation_keys
    # federation_key should be updated to the new key
    assert orch.federation_key == newkey
    # the previous key remains in the active list
    assert oldkey in orch.active_federation_keys

    # wait a second to avoid replay detection on the next broadcast
    time.sleep(1)
    # modify local dictionary so new advertisement hash differs from earlier one
    mgr.update_local_dictionary('nodeK', b'ADDITIONAL')
    mgr.federated_aggregation(use_privacy=False)
    # prepare new payload after rotation
    payload2 = mgr.prepare_advertisement()
    # sign payload2 with the old key and broadcast
    sig_old_again = sign_payload(payload2, oldkey)
    res_old = fed.broadcast_dictionary(payload2['hash'], 'nodeK', pattern_count=(payload2['pattern_count'], payload2['timestamp']), signature=sig_old_again)
    assert res_old.get('rejected') is not True

    # prepare another distinct payload for the new key
    time.sleep(1)
    mgr.update_local_dictionary('nodeK', b'MORE')
    mgr.federated_aggregation(use_privacy=False)
    payload3 = mgr.prepare_advertisement()
    sig_new = sign_payload(payload3, newkey)
    res_new = fed.broadcast_dictionary(payload3['hash'], 'nodeK', pattern_count=(payload3['pattern_count'], payload3['timestamp']), signature=sig_new)
    assert res_new.get('rejected') is not True

    # rotate again but keep_old=0, dropping previous keys
    finalkey = orch.rotate_federation_key(keep_old=0)
    assert finalkey in orch.active_federation_keys
    assert len(orch.active_federation_keys) == 1
    # any signature signed with the earlier keys should now be rejected
    res3 = fed.broadcast_dictionary(payload2['hash'], 'nodeK', pattern_count=(payload2['pattern_count'], payload2['timestamp']), signature=sig_old_again)
    assert res3.get('rejected') is True
    res4 = fed.broadcast_dictionary(payload3['hash'], 'nodeK', pattern_count=(payload3['pattern_count'], payload3['timestamp']), signature=sig_new)
    assert res4.get('rejected') is True
