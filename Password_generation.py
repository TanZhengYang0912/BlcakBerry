import random
import string
def generate_password(length=12):
  if length < 8:
    raise ValueError("Password length should be at least 8 characters.")
  
  characters = string.ascii_letters + string.digits + string.punctuation
  password = ''.join(random.choice(characters)
for _ in range(length))
  return password
if __name__ == "__main__":
  length = int(input("Enter the desired password length: "))
  print(f"Generated Password:{generate_password(length)}")