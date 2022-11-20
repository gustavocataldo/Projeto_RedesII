import threading
import socket

HOST_IP = '127.0.0.1'
PORT = 55556
nickname = input('Choose a nickname: ')

def handle_messages(conn: socket.socket):
    while True:
        try:
            message = conn.recv(1024).decode('ascii')
            if message == 'NICK':
                conn.send(nickname.encode('ascii'))
            elif message == 'CONNECTION_CLOSED':
                break
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