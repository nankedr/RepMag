import os
from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

if not os.path.exists('userskey'):
    context = create_context('secp256k1')
    with open('userskey', 'w') as f:
        for i in range(0, 100):
            private_key = context.new_random_private_key()
            print(private_key.as_hex())
            f.write(private_key.as_hex()+'\n')

with open('userskey', 'r') as f:
    signer_list = [line.rstrip('\n') for line in f.readlines()]

print(signer_list)

if not os.path.exists('users_pub_key'):
    context = create_context('secp256k1')
    with open('users_pub_key', 'w') as f:
        for key in signer_list:
            pub_key = CryptoFactory(context).new_signer(Secp256k1PrivateKey.from_hex(
                key)).get_public_key().as_hex()
            f.write(pub_key + ' ' + '1' + '\n')

