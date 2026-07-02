from cryptography.fernet import Fernet
# Generate a key for encryption and decryption
def generate_key():
  key = Fernet.generate_key()
  with open("secret.key", "wb") as key_file:
    key_file.write(key)

# Load the previously generated key
def load_key():
  return open("secret.key", "rb").read()

# Encrypt a message
def encrypt_message(message):
  key = load_key()
  fernet = Fernet(key)
  encrypted_message = fernet.encrypt(message.encode())
  return encrypted_message

# Decrypt a message
def decrypt_message(encrypted_message):
  key = load_key()
  fernet = Fernet(key)
  decrypted_message = fernet.decrypt(encrypted_message).decode()
  return decrypted_message

if __name__ == "__main__":
# Generate a key (run this only once)
  generate_key()
# Example message
  message = "Hello, this is a secret message!"
# Encrypt the message
  encrypted = encrypt_message(message)
  print(f"Encrypted: {encrypted}")
# Decrypt the message
  decrypted = decrypt_message(encrypted)
  print(f"Decrypted: {decrypted}")