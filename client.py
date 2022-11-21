import threading
import socket

HOST_IP = '127.0.0.1'
PORT = 5000
BUFFER_SIZE = 1024

connections_must_be_closed = threading.Event()

nickname = None
class ConexaoEncerrada(Exception):
    pass

instrucoes = f"""
            Instruçoes de uso:
                /quit: Sair da sala
                /consulta <nickname>: Consultar os dados de outro usuário\n\n"""

def initialize_udp_socket() -> socket.socket:
    audio_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return audio_client_socket

def initialize_tcp_socket() -> socket.socket:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST_IP, PORT))
    return client_socket

def close_sockets(client_socket: socket.socket, udp_client: socket.socket):
    client_socket.shutdown(socket.SHUT_RDWR)
    udp_client.shutdown(socket.SHUT_RDWR)
    client_socket.close()
    udp_client.close()

def handle_messages(conn: socket.socket, udp_conn: socket.socket, my_nickname: str):
    while True:
        try:
            message = conn.recv(1024).decode('ascii')
            if message == 'CONNECTION_CLOSED':
                connections_must_be_closed.set()
                break
            elif message == 'NICKNAME_NOT_FOUND':
                print('O usuário consultado não existe.')
            elif message.split('|')[0] == 'QUERY_RESULT':
                address, port, nickname = message.split('|')[1].split('-')
                print(f'Endereço: {address} | Porta: {port}')
                if nickname != my_nickname:
                    udp_conn.sendto(str.encode('testeee'), (address, int(port)))
            else:
                print(message)
        except Exception as exc:
            error_message = f'Houve um erro processando a mensagem do servidor | exc: {str(exc)}'
            print(error_message)
            break

def handle_udp(udp_conn: socket.socket):
    while True:
        try:
            if connections_must_be_closed.is_set(): break
            msg, address = udp_conn.recvfrom(BUFFER_SIZE)
            _msg = msg.split()
            username, address, porta = _msg
            if msg[0]== 'INVITE':
                print(f'Você foi convidado para uma ligação com o usuário {username} ({address}, {porta}). Deseja aceitar?')
        except Exception as exc:
            pass

def client() -> None:
    try:
        client_socket = initialize_tcp_socket()
        udp_client_socket = initialize_udp_socket()
        nickname_valid: bool = False
        my_info = None
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
            
            while not my_info:
                msg = client_socket.recv(1024).decode('ascii')
                client_socket.send(('/consulta ' + nickname).encode('ascii'))
                if msg.split('|')[0] == 'QUERY_RESULT':
                    address, port, nickname = msg.split('|')[2].split('-')
                    my_info = (address, port, nickname)
                    udp_client_socket.bind((address, int(port)))

            udp_thread: threading.Thread = threading.Thread(target=handle_udp, args=[udp_client_socket])
            thread: threading.Thread = threading.Thread(target=handle_messages, args=[client_socket, udp_client_socket, nickname])
            thread.start()
            udp_thread.start()

            while True:
                msg = input()
                client_socket.send(msg.encode('ascii'))
                if msg == '/quit':
                    thread.join()
                    try:
                        udp_thread.join()
                    except:
                        raise ConexaoEncerrada
                    raise ConexaoEncerrada
        
        close_sockets(client_socket, udp_client_socket)
    except ConexaoEncerrada:
        print('Conexão encerrada.')
        close_sockets(client_socket, udp_client_socket)
    except Exception as exc:
        error_message = f'Houve um erro durante a conexão com o servidor | exc: {str(exc)}'
        print(error_message)
        close_sockets(client_socket, udp_client_socket)



client()