import bcrypt
import sys

def generate_hash(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(generate_hash(password))
    else:
        print("Uso: python generate_hash.py <password>")
