import hashlib
import random
import os
import struct
from Crypto.Cipher import AES

# Adapted from Eli Bendersky's intro to AES encryption using PyCrypto:
# https://eli.thegreenplace.net/2010/06/25/aes-encryption-of-files-in-python-with-pycrypto

COOKIE = 'CRYDB001'


def encrypt(key, in_filename, out_filename, chunk_size=64*1024):
    """ Encrypts an arbitrary string of bytes using AES (CBC mode) with the
        given key.

        key:
            The encryption key - a string that must be either 16, 24 or 32
            bytes long. Longer keys are more secure.

        in_filename:
            The filename of the file that contains the data to be encrypted.

        out_filename:
            The file to be written, containing the encrypted data.

        chunk_size:
            Sets the size of the chunk which the function uses to encrypt the
            data. Larger chunk sizes can be faster for some files and machines.
            chunk_size must be divisible by 16.
    """

    iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
    encryptor = AES.new(key, AES.MODE_CBC, iv)
    data_size = os.path.getsize(in_filename)

    with open(in_filename, 'rb') as infile:
        with open(out_filename, 'wb') as outfile:
            outfile.write(COOKIE)
            outfile.write(struct.pack('<Q', data_size))
            outfile.write(iv)

            while True:
                chunk = infile.read(chunk_size)
                if len(chunk) == 0:
                    break
                elif len(chunk) % 16 != 0:
                    chunk += ' ' * (16 - len(chunk) % 16)

                outfile.write(encryptor.encrypt(chunk))


def decrypt(key, in_filename, out_filename, chunk_size=24*1024):
    """ Decrypts a file using AES (CBC mode) with the given key.
        key:
            The encryption key - a string that must be either 16, 24 or 32
            bytes long. Longer keys are more secure.

        in_filename:
            The filename of the file that contains the data to be decrypted.

        out_filename:
            The file to be written, containing the decrypted data.

        chunk_size:
            Sets the size of the chunk which the function uses to encrypt the
            data. Larger chunk sizes can be faster for some files and machines.
            chunk_size must be divisible by 16.
    """

    with open(in_filename, 'rb') as infile:
        cookie = infile.read(len(COOKIE))
        if cookie != COOKIE:
            raise Exception("Input file does not have expected cookie")

        orig_size = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
        iv = infile.read(16)
        decryptor = AES.new(key, AES.MODE_CBC, iv)

        with open(out_filename, 'wb') as outfile:
            while True:
                chunk = infile.read(chunk_size)
                if len(chunk) == 0:
                    break
                outfile.write(decryptor.decrypt(chunk))

            outfile.truncate(orig_size)


def main():
    plaintext = ("Lorem Ipsum is simply dummy text of the printing and "
                 "typesetting industry. Lorem Ipsum has been the industry's "
                 "standard dummy text ever since the 1500s, when an unknown "
                 "printer took a galley of type and scrambled it to make a "
                 "type specimen book. It has survived not only five centuries, "
                 "but also the leap into electronic typesetting, remaining "
                 "essentially unchanged. It was popularised in the 1960s with "
                 "the release of Letraset sheets containing Lorem Ipsum "
                 "passages, and more recently with desktop publishing software "
                 "like Aldus PageMaker including versions of Lorem Ipsum.")

    password = 's3krit pa55wort!'
    key = hashlib.sha256(password).digest()
    plaintext_filename = 'lorem-encryptum.txt'
    ciphertext_filename = 'lorem-encryptum.enc'

    with open(plaintext_filename, 'wb') as ptfile:
        ptfile.write(plaintext)

    encrypt(key, plaintext_filename, ciphertext_filename)
    decrypt(key, ciphertext_filename, plaintext_filename)

    with open(plaintext_filename, 'rb') as ptfile:
        rt_plaintext = ptfile.read()

    if rt_plaintext != plaintext:
        print("Round-trip plaintext doesn't match original?!")
    else:
        print("Round-trip plaintext matches original")


if __name__ == "__main__":
    main()
