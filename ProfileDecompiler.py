from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import zlib

def decompile():
    # Constants based on provided JavaScript code
    DUMMY_HEADER_LENGTH = 44
    PASSWORD_INDEX_LENGTH = 8
    SALT_LENGTH = 24
    KEY_LENGTH = 16
    IV_LENGTH = 16
    DERIVE_ITERATIONS = 10
    PASSWORD = '11'

    # Read the input file
    input_path = 'Profile.Save'
    output_path = 'Decrypted_Profile.json'

    with open(input_path, 'rb') as f:
        bytes_data = f.read()

    # Extract salt and encrypted bytes
    salt_start = DUMMY_HEADER_LENGTH + PASSWORD_INDEX_LENGTH
    salt_end = salt_start + SALT_LENGTH
    salt = bytes_data[salt_start:salt_end]
    encrypted_bytes = bytes_data[salt_end:]

    # Derive key and IV
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA1(),
        length=KEY_LENGTH + IV_LENGTH,
        salt=salt,
        iterations=DERIVE_ITERATIONS,
        backend=default_backend()
    )
    derived_bytes = kdf.derive(PASSWORD.encode())
    iv = derived_bytes[:IV_LENGTH]
    key = derived_bytes[IV_LENGTH:IV_LENGTH + KEY_LENGTH]

    # Decrypt the data
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

    # Decompress the data
    try:
        decompressed_data = zlib.decompress(decrypted_bytes)
        print("Decompression successful")
    except zlib.error as e:
        print("Decompression error:", e)
        decompressed_data = b''

    # Write the output file
    if decompressed_data:
        with open(output_path, 'wb') as f:
            f.write(decompressed_data)
        