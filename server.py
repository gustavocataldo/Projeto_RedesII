import threading
import socket
from collections import namedtuple
from typing import Dict, List

HOST = '127.0.0.1'
PORT = 5000
UDP_PORT = 6000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((HOST, PORT))
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

def get_client_by_nickname(nickname: str, clients: Dict[str, Client]) -> Client:
    return clients.get(nickname)

def handle(client: Client, clients: Dict[str, Client]):
    while True:
        try:
            client_socket: socket.socket = client.socket
            message = receive_decoded_message(client_socket)
            if message == '/quit':
                nickname_to_remove: str = client.nickname
                print(f'{nickname_to_remove} disconnected')
                send_encoded_message(client_socket, 'CONNECTION_CLOSED')
                
                del clients[nickname_to_remove]

                broadcast(clients, f'{nickname_to_remove} left the chat')
                broadcast_registry_table(clients)
                
                break

            elif message.split()[0] == '/consulta':
                nickname = message.split()[1]
                _client: Client = get_client_by_nickname(nickname, clients)
                client_msg = f'QUERY_RESULT|{client.port}-{client.address}-{nickname}' if _client else 'NICKNAME_NOT_FOUND'
                send_encoded_message(client_socket, client_msg)

        except Exception as exc:
            print(str(exc))
            nickname = client.nickname
            if clients.get(nickname):
                del clients[nickname]
            broadcast(clients, f'{nickname} left the chat')
            print(f'{nickname} left the chat')
            broadcast_registry_table(clients)
            break

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

        
        clients.setdefault(nickname, Client(socket=client, port=client_port, address=client_address, nickname=nickname))
       
        send_encoded_message(client, 'CLIENT_CONNECTED\n')

        thread = threading.Thread(target=handle, args=(clients[nickname], clients))
        thread.start()

        broadcast_registry_table(clients)
        broadcast(clients, message=f'{nickname} joined the chat.')

print('Server listening')
receive(clients)