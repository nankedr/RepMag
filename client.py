import os
import random
from hashlib import sha512
import urllib.request
from urllib.error import HTTPError
import cbor

import time

from sawtooth_signing import create_context
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from sawtooth_signing import CryptoFactory
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchList

NUM_USERS = 6


def make_BCMCS_transaction(signer, payload):
    payload_bytes = cbor.dumps(payload)

    # sha512('bcmcs'.encode('utf-8')).hexdigest()[0:6] == 'e92c0c'
    txn_header_bytes = TransactionHeader(
        family_name='bcmcs',
        family_version='1.0',
        inputs=['e92c0c'],
        outputs=['e92c0c'],
        signer_public_key=signer.get_public_key().as_hex(),
        batcher_public_key=signer.get_public_key().as_hex(),
        dependencies=[],
        payload_sha512=sha512(payload_bytes).hexdigest()
    ).SerializeToString()

    signature = signer.sign(txn_header_bytes)

    txn = Transaction(
        header=txn_header_bytes,
        header_signature=signature,
        payload=payload_bytes
    )

    txns = [txn]

    batch_header_bytes = BatchHeader(
        signer_public_key=signer.get_public_key().as_hex(),
        transaction_ids=[txn.header_signature for txn in txns],
    ).SerializeToString()

    signature = signer.sign(batch_header_bytes)

    batch = Batch(
        header=batch_header_bytes,
        header_signature=signature,
        transactions=txns
    )

    batch_list_bytes = BatchList(batches=[batch]).SerializeToString()
    return batch_list_bytes

def send_tras(tras_bytes):
    try:
        request = urllib.request.Request(
            'http://localhost:8008/batches',
            tras_bytes,
            method='POST',
            headers={'Content-Type': 'application/octet-stream'})
        response = urllib.request.urlopen(request)

    except HTTPError as e:
        response = e.file

    return response.read().decode('utf-8')

def init_reputation():
    context = create_context('secp256k1')
    private_key = context.new_random_private_key()
    signer = CryptoFactory(context).new_signer(private_key)

    payload = {
        'TaskID': 0,
        'Verb': 'init',
        'Name': 'usernum',
        'Value': 2}
    r = send_tras(make_BCMCS_transaction(signer, payload))

    print(r)


def gen_sensed_data():
    sensed_data = [10, 30] * (NUM_USERS//2)
    blind_key = []
    with open('users_blind_key') as f:
        for i in range(0, NUM_USERS):
            blind_key.append(int(f.readline().rstrip('\n')))
    return [a+b for a, b in zip(sensed_data, blind_key)]


#签名密钥列表
context = create_context('secp256k1')
with open('userskey', 'r') as f:
    signer_list = [CryptoFactory(context).new_signer(
    Secp256k1PrivateKey.from_hex(f.readline().rstrip('\n'))) for i in range(0, NUM_USERS)]


#感知数据列表
sensed_data_list = gen_sensed_data()

#初始化信誉值
#init_reputation()

start = time.clock()
#每个感知用户发送数据
for signer, sensed_data in zip(signer_list, sensed_data_list):
    print('{}:{}'.format(signer.get_public_key().as_hex(), sensed_data))
    payload = {
        'TaskID': 0,
        'Verb': 'set',
        'Name': 'sensing',
        'Value': sensed_data}

    batch_list_bytes = make_BCMCS_transaction(signer, payload)

    r = send_tras(batch_list_bytes)
    time.sleep(0.1)

    print(r)

time.sleep(0.1)

# payload = {
#         'TaskID': 0,
#         'Verb': 'aggregation',
#         'Name': 'sensing',
#         'Value': NUM_USERS}

payload = {
        'TaskID': 0,
        'Verb': 'average',
        'Name': 'sensing',
        'Value': NUM_USERS}

r = send_tras(make_BCMCS_transaction(signer, payload))
print(r)
end = time.clock()
print(end-start)