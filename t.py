import os

if not os.path.exists('users_blind_key'):
    with open('users_blind_key', 'w') as f:
        for i in range(0, 100):
            num = int.from_bytes(os.urandom(8), byteorder='little')
            f.write(str(num) + '\n')
