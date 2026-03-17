
import os

def check_encodings(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py') or file.endswith('.sql') or file.endswith('.env'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError as e:
                    print(f"Error en {path}: {e}")

if __name__ == "__main__":
    check_encodings('.')
