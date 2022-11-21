import threading
import socket

HOST_IP = '127.0.0.1'
PORT = 5000

instrucoes = f"""
            Instruçoes de uso:
                /quit: Sair da sala
                /consulta <nickname>: Consultar os dados de outro usuário\n\n"""

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
            else:
                print(message)
        except Exception as exc:
            conn.close()
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
            thread = threading.Thread(target=handle_messages, args=[client_socket])
            thread.start()

            while True:
                msg = input()
                client_socket.send(msg.encode('ascii'))
                if msg == '/quit':
                    print('Conexão encerrada.')
                    break

        
        client_socket.close()

    except Exception as exc:
        error_message = f'Houve um erro durante a conexão com o servidor | exc: {str(exc)}'
        print(error_message)
        client_socket.close()


client()