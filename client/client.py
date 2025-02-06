import config
from network import ChatClient

def main():
    print("Starting client...")
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    client = ChatClient(host, port)

if __name__ == "__main__":
    main()