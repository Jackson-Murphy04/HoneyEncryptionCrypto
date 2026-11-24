"""Conventional password-based authenticated-encryption comparison.

AES-256-GCM + scrypt is intentionally a baseline, not a honey-encryption
construction: wrong passwords normally raise InvalidTag instead of returning
plausible decoys. Requires the `cryptography` package.
"""
from __future__ import annotations
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_BYTES=16
NONCE_BYTES=12
KEY_BYTES=32
SCRYPT_N=2**14
SCRYPT_R=8
SCRYPT_P=1

def _key(password: str, salt: bytes) -> bytes:
    if not isinstance(password,str) or not password:
        raise ValueError('Password must be a non-empty string')
    return __import__('hashlib').scrypt(password.encode('utf-8'),salt=salt,n=SCRYPT_N,r=SCRYPT_R,p=SCRYPT_P,dklen=KEY_BYTES)

def encrypt(plaintext: str, password: str) -> dict:
    salt=os.urandom(SALT_BYTES); nonce=os.urandom(NONCE_BYTES)
    ciphertext=AESGCM(_key(password,salt)).encrypt(nonce,plaintext.encode('utf-8'),b'HE-BASELINE-v1')
    return {'version':1,'salt':salt.hex(),'nonce':nonce.hex(),'ciphertext':ciphertext.hex()}

def decrypt(record: dict, password: str) -> str:
    if set(record)!={'version','salt','nonce','ciphertext'} or record['version']!=1:
        raise ValueError('Invalid baseline record')
    salt=bytes.fromhex(record['salt']); nonce=bytes.fromhex(record['nonce']); ct=bytes.fromhex(record['ciphertext'])
    if len(salt)!=SALT_BYTES or len(nonce)!=NONCE_BYTES: raise ValueError('Invalid salt or nonce length')
    return AESGCM(_key(password,salt)).decrypt(nonce,ct,b'HE-BASELINE-v1').decode('utf-8')
