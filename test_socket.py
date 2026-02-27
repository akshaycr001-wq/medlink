import socket
import sys

def test_socket():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print("Socket created.")
        s.bind(('127.0.0.1', 5015))
        print("Socket bound to 5015.")
        s.listen(1)
        print("Socket listening...")
        s.close()
        print("Socket test passed.")
    except Exception as e:
        print(f"Socket error: {e}")

if __name__ == "__main__":
    test_socket()
