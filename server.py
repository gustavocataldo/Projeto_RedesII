import threading
import socket
from collections import namedtuple
from typing import Dict

host = '127.0.0.1'
port = 55556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

Client = namedtuple('Client', ['socket', 'port', 'address', 'nickname'])
clients: Dict[str, Client] = {}

def broadcast(clients: Dict[str, Client], message: str):
    for client_data in clients.values():
        client_data.socket.send(message.encode('ascii'))

def broadcast_registry_table(clients: Dict[str, Client]) -> str:
    tabela = 'NICKNAME             ADDRESS             PORT\n'
    for nickname, info in clients.items():
            tabela = tabela + f'{nickname}             {info.address}             {info.port}\n'
    broadcast(clients, tabela)

def ask_for_client_nickname(client: socket.socket, id: int) -> str:
    msg = 'NICK' if id == 0 else 'NICKNAME_ALREADY_TAKEN'
    send_encoded_message(client, msg)
    nickname = receive_decoded_message(client)
    print(f'Nickname of the client is {nickname}')
    return nickname

def receive_decoded_message(client: socket.socket) -> str:
    message = client.recv(1024)
    return message.decode('ascii')

def send_encoded_message(client: socket.socket, message: str):
    client.send(message.encode('ascii'))

def nickname_already_taken(nickname: str, clients: Dict[str, Client]) -> bool:
    return nickname in clients.keys()

def handle(client: Client, clients: Dict[str, Client]):
    while True:
        try:
            client_socket: socket.socket = client.socket
            message = receive_decoded_message(client_socket)
            if message == '/quit':
                send_encoded_message(client_socket, 'CONNECTION_CLOSED')
                del clients[client.nickname]
                client_socket.close()
                print(f'{client.nickname} disconnected')
                broadcast(clients, f'{client.nickname} left the chat'.encode('ascii'))
                broadcast_registry_table(clients)
                
                break

        except Exception as exc:
            print(str(exc))

def receive(clients: Dict[str, Client]):
    while True:
        client, address = server.accept()
        client_port, client_address = address
        print(f'Connected to {str(address)}')
        
        nickname = ask_for_client_nickname(client, 0)
        valid_nickname: bool = not nickname_already_taken(nickname, clients)
        
        while not valid_nickname:
            nickname = ask_for_client_nickname(client, -1)
            valid_nickname = not nickname_already_taken(nickname, clients)

        clients.setdefault(nickname, Client(client, client_port, client_address, nickname))
        send_encoded_message(client, 'CLIENT_CONNECTED\n')

        thread = threading.Thread(target=handle, args=(clients[nickname], clients))
        thread.start()

        broadcast_registry_table(clients)
        broadcast(clients, message=f'{nickname} joined the chat.')

print('Server listening')
receive(clients)