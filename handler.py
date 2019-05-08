import logging
import hashlib
import math
import cbor
import numpy as np
import random

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError


LOGGER = logging.getLogger(__name__)



NUM_USERS = 2

VALID_VERBS = 'set', 'init', 'aggregation', 'average'
MIN_VALUE = -2**64
MAX_VALUE = 2**64
MAX_NAME_LENGTH = 50

FAMILY_NAME = 'bcmcs'


BCMCS_ADDRESS_PREFIX = hashlib.sha512(
    FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]

def make_reputation_address(pub_key):
    return BCMCS_ADDRESS_PREFIX + hashlib.sha512(pub_key.encode('utf-8')).hexdigest()[0:64]

def make_bcmcs_address(name):
    return BCMCS_ADDRESS_PREFIX + hashlib.sha512(name.encode('utf-8')).hexdigest()[0:64]

#持久化的是全局信誉值

class BCMCSTransactionHandler(TransactionHandler):

    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [BCMCS_ADDRESS_PREFIX]


    def apply(self, transaction, context):
        header = transaction.header
        signer = header.signer_public_key

        payload = self._unpack_transaction(transaction)

        #初始化信誉值
        if payload['Verb'] == 'init':
            print('init...............................')

            # 签名密钥列表
            with open('users_pub_key', 'r') as f:
                for line in f:
                    pk, ran = line.rstrip('\n').split()
                    rep_addr = make_reputation_address(pk)
                    ran = int(ran)
                    context.set_state({rep_addr: cbor.dumps(ran)})

        #存储感知数据
        elif payload['Verb'] == 'set':
            print('set...............................')
            addr = make_bcmcs_address(str(payload['TaskID']) + signer + 'aggregation')
            context.set_state({addr: cbor.dumps(payload['Value'])})

        #聚合感知数据
        elif payload['Verb'] == 'aggregation':
            i = 0
            weight_of_average = 0
            sum_rep = 0

            sum_blind = 0
            with open('users_pub_key', 'r') as f, open('users_blind_key') as f1:
                for line in f:
                    if i < int(payload['Value']):
                        pk = line.rstrip('\n').split()[0]
                        rep_addr = make_reputation_address(pk)
                        rep = cbor.loads((context.get_state([rep_addr]))[0].data)

                        data_addr = make_bcmcs_address(str(payload['TaskID']) + pk + 'aggregation')
                        data = cbor.loads((context.get_state([data_addr]))[0].data)

                        sum_rep += rep
                        weight_of_average += data * rep

                        sum_blind += int(f1.readline().rstrip('\n')) * rep

                        i += 1
            print('weight_of_average:{}, sum_rep:{}'.format(weight_of_average, sum_rep))

            # 聚合操作
            weight_of_average = (weight_of_average - sum_blind) / sum_rep


            context.set_state({make_bcmcs_address(str(payload['TaskID']) + 'aggregation'): cbor.dumps(weight_of_average)})
            print('weight of ave: {}'.format(weight_of_average))

        # 聚合感知数据
        elif payload['Verb'] == 'average':
            i = 0
            average = 0

            sum_blind = 0
            with open('users_pub_key', 'r') as f, open('users_blind_key') as f1:
                for line in f:
                    if i < int(payload['Value']):
                        pk = line.rstrip('\n').split()[0]

                        data_addr = make_bcmcs_address(str(payload['TaskID']) + pk + 'aggregation')
                        data = cbor.loads((context.get_state([data_addr]))[0].data)

                        average += data

                        #sum_blind += int(f1.readline().rstrip('\n'))

                        i += 1
            print('average:{}, sum:{}'.format(average, i))

            # 聚合操作
            average /= i

            context.set_state(
                {make_bcmcs_address(str(payload['TaskID']) + 'average'): cbor.dumps(average)})
            print('ave: {}'.format(average))
        else:
            print('else')


    def _unpack_transaction(self, transaction):

        try:

            payload = self._decode_data(transaction)

        except:
            raise InvalidTransaction("Invalid payload serialization")

        self._validate_para(payload)

        return payload


    def _decode_data(self, transaction):
        try:
            content = cbor.loads(transaction.payload)
        except:
            raise InvalidTransaction('Invalid payload serialization')

        if 'TaskID' not in content:
            raise InvalidTransaction('TaskID is required')

        if 'Verb' not in content:
            raise InvalidTransaction('Verb is required')

        if 'Name' not in content:
            raise InvalidTransaction('Name is required')

        if 'Value' not in content:
            raise InvalidTransaction('Value is required')

        return content


    def _validate_para(self, payload):
        if payload['Verb'] not in VALID_VERBS:
            raise InvalidTransaction('Verb must be "set", "init"')

        if not isinstance(payload['Name'], str) or len(payload['Name']) > MAX_NAME_LENGTH:
            raise InvalidTransaction(
                'Name must be a string of no more than {} characters'.format(
                    MAX_NAME_LENGTH))

        if not isinstance(payload['Value'], int) or payload['Value'] < MIN_VALUE or payload['Value'] > MAX_VALUE:
            raise InvalidTransaction(
                'Value must be an integer '
                'no less than {i} and no greater than {a}'.format(
                    i=MIN_VALUE,
                    a=MAX_VALUE))

        if not isinstance(payload['TaskID'], int):
            raise InvalidTransaction('TaskID must be an integer ')
