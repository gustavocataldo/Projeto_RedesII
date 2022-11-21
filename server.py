import threading
import socket
from collections import namedtuple
from typing import Dict, List

HOST = '127.0.0.1'
PORT = 5000
UDP_PORT = 6000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def initialize_audio_server():
    audio_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    audio_server.bind(HOST, UDP_PORT)
    audio_server.listen()

server.bind((HOST, PORT))
server.listen()

Client = namedtuple('Client', ['socket', 'port', 'address', 'nickname', 'convites_recebidos', 'convites_enviados'])
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
                client_msg = f'QUERY_RESULT|{client.port}-{client.address}' if _client else 'NICKNAME_NOT_FOUND'
                send_encoded_message(client_socket, client_msg)
            
            elif message.split()[0] == '/convite':
                nickname = message.split()[1]
                _client: Client = get_client_by_nickname(nickname, clients)
                if not _client:
                    send_encoded_message(client.socket, 'NICKNAME_NOT_FOUND')
                else:
                    _message = f"Voce foi convidado para um voice chat com o usuario '{client.nickname}'. /aceitar_convite <nickname> ou /rejeitar_convite <nickname>"
                    if nickname not in client.convites_recebidos: client.convites_recebidos.append(client.nickname)
                    send_encoded_message(_client.socket, _message)
            elif message.split()[0] == '/aceitar_convite':
                nickname = message.split()[1]
                _client: Client = get_client_by_nickname(nickname, clients)
                if not _client:
                    send_encoded_message(client.socket, 'USER_LEFT_THE_ROOM')
                elif _client and nickname not in _client.convites_recebidos:
                    send_encoded_message(client.socket, 'INVITE_NOT_FOUND')
                else:
                    send_encoded_message(_client.socket, 'INVITE_ACCEPTED')
                    send_encoded_message(client.socket, 'INVITE_ACCEPTED')
                    id_convite = _client.convites_recebidos.index(nickname)
                    _client.convites_recebidos.pop(id_convite)

            elif message.split()[0] == '/rejeitar_convite':
                nickname = message.split()[1]
                _client: Client = get_client_by_nickname(nickname, clients)
                if not _client:
                    send_encoded_message(client.socket, 'USER_LEFT_THE_ROOM')
                elif _client and nickname in _client.convites_recebidos:
                    id_convite = _client.convites_recebidos.index(nickname)
                    _client.convites_recebidos.pop(id_convite)
                    send_encoded_message(_client.socket, 'INVITE_REJECTED')


        except Exception as exc:
            print(str(exc))
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

        clients.setdefault(nickname, Client(client, client_port, client_address, nickname, [], []))
        send_encoded_message(client, 'CLIENT_CONNECTED\n')

        thread = threading.Thread(target=handle, args=(clients[nickname], clients))
        thread.start()

        broadcast_registry_table(clients)
        broadcast(clients, message=f'{nickname} joined the chat.')

print('Server listening')
receive(clients)