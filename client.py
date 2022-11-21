import threading
import socket

HOST_IP = '127.0.0.1'
PORT = 5000

class ConexaoEncerrada(Exception):
    pass

instrucoes = f"""
            Instruçoes de uso:
                /quit: Sair da sala
                /consulta <nickname>: Consultar os dados de outro usuário\n\n"""

def initialize_audio_client():
    audio_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def close_socket(client_socket: socket.socket):
    client_socket.shutdown(socket.SHUT_RDWR)
    client_socket.close()

def handle_messages(conn: socket.socket):
    while True:
        try:
            message = conn.recv(1024).decode('ascii')
            if message == 'CONNECTION_CLOSED':
                break
            elif message == 'NICKNAME_NOT_FOUND':
                print('O usuário consultado não existe.')
            elif message.split('|')[0] == 'QUERY_RESULT':
                address, port = message.split('|')[1].split('-')
                print(f'Endereço: {address} | Porta: {port}')
            elif message == 'USER_LEFT_THE_ROOM':
                print('O usuário deixou a sala ou não existe no registro.')
            elif message == 'INVITE_NOT_FOUND':
                print('Não há um convite ativo deste usuário para você.')
            elif message == 'INVITE_ACCEPTED':
                print('Convite foi aceito. Inicializando client de áudio')
            elif message == 'INVITE_REJECTED':
                print('Usuário destino está ocupado')
            else:
                print(message)
        except Exception as exc:
            error_message = f'Houve um erro processando a mensagem do servidor | exc: {str(exc)}'
            print(error_message)
            break

def client() -> None:
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST_IP, PORT))
        nickname_valid: bool = False
        print(instrucoes)
        while not nickname_valid:
            msg = client_socket.recv(1024).decode('ascii')
            if msg == 'NICK':
                nickname = input('Choose a nickname: ')
                client_socket.send(nickname.encode('ascii'))
            elif msg == "NICKNAME_ALREADY_TAKEN":
                print('Esse nick já está em uso, por favor escolha outro')
                nickname = input('Choose a nickname: ')
                client_socket.send(nickname.encode('ascii'))
            else:
                nickname_valid = True
        
        if nickname_valid:
            thread: threading.Thread = threading.Thread(target=handle_messages, args=[client_socket])
            thread.start()

            while True:
                msg = input()
                client_socket.send(msg.encode('ascii'))
                if msg == '/quit':
                    thread.join()
                    raise ConexaoEncerrada
        
        close_socket(client_socket)
    except ConexaoEncerrada:
        print('Conexão encerrada.')
        close_socket(client_socket)
    except Exception as exc:
        error_message = f'Houve um erro durante a conexão com o servidor | exc: {str(exc)}'
        print(error_message)
        close_socket(client_socket)



client()