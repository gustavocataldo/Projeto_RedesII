import threading
import socket
import queue
import pyaudio


HOST_IP = '127.0.0.1'
PORT = 5000
BUFFER_SIZE = 1024

frames = []

connections_must_be_closed = threading.Event()
nickname = None
must_kill_audio_threads = threading.Event()


class ConexaoEncerrada(Exception):
    pass


instrucoes = f"""
            Instruçoes de uso:
                /quit: Sair da sala
                /consulta <nickname>: Consultar os dados de outro usuário\n\n"""


def return_audio_stream(input=False):

    return pyaudio.PyAudio().open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        output=not input,
        input=input,
        frames_per_buffer=BUFFER_SIZE
    )


def record_audio(stream):
    while True:
        frames.append(stream.read(BUFFER_SIZE))


def stream_audio(udp_socket: socket.socket, address: tuple):
    while True:
        if len(frames) > 0:
            try:
                udp_socket.sendto(frames.pop(0), address)
            except IndexError:
                pass


def play_audio(stream):
    while True:
        if len(frames) == 10:
            while True:
                try:
                    stream.write(frames.pop(0), BUFFER_SIZE)
                except IndexError:
                    pass


def initialize_udp_socket(address: tuple) -> socket.socket:
    audio_client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    audio_client_socket.bind(address)
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
                found_client = message.split('|')[1].split('-')
                address, port, nickname = found_client
                print(f'Endereço: {address} | Porta: {port}')
                if nickname != my_nickname:
                    print('Enviando um convite para chamada de voz ao usuário!')
                    udp_conn.sendto(str.encode(
                        f'INVITE-{my_nickname}'), (address, int(port)))
            else:
                print(message)
        except Exception as exc:
            error_message = f'Houve um erro processando a mensagem do servidor | exc: {str(exc)}'
            print(error_message)
            break


def handle_udp(udp_conn: socket.socket, queue: queue.Queue):
    while True:
        try:
            if connections_must_be_closed.is_set():
                break
            msg, address = udp_conn.recvfrom(int(BUFFER_SIZE*2))
            if len(msg) < BUFFER_SIZE * 2:
                msg = msg.decode('ascii').split('-')
            if msg[0] == 'INVITE':
                sender_nickname = msg[1]
                sender_address = address
                print(
                    f'Você foi convidado para uma ligação com o usuário {sender_nickname} {sender_address}. Deseja aceitar? ( /aceitar ou /rejeitar )')
                resposta = queue.get()
                if resposta == '/aceitar':
                    udp_conn.sendto(
                        f'/convite_aceito-{udp_conn.getsockname()}'.encode('ascii'), sender_address)
                    udp_conn.sendto(
                        f'/convite_aceito-{sender_address}'.encode('ascii'), udp_conn.getsockname())
                else:
                    udp_conn.sendto(
                        '/rejeitar'.encode('ascii'), sender_address)

            elif msg[0] == '/convite_aceito':
                address_destino = eval(msg[1])
                my_address = udp_conn.getsockname()
                print(f'ORIGEM: {my_address} | DESTINO: {address_destino}')
                print('Convite aceito! Inicializando chamada de voz...')
                initialize_audio_threads(udp_conn, address_destino)

                while queue.get() != '/encerrar_ligacao':
                    pass

                print('Ligação encerrada.')
                must_kill_audio_threads.set()

            elif msg[0] == '/rejeitar':
                print('O usuário está ocupado no momento.')
        except Exception as exc:
            pass


def initialize_audio_threads(udp_socket: socket.socket, address_destino: tuple):
    audio_stream = return_audio_stream(input=True)
    threading.Thread(target=record_audio, args=[audio_stream]).start()
    threading.Thread(target=stream_audio, args=[
                     udp_socket, address_destino]).start()
    output_audio_stream = return_audio_stream(input=False)
    threading.Thread(target=play_audio, args=[output_audio_stream]).start()


def handle_input(tcp_socket: socket.socket, queue: queue.Queue):
    while True:
        msg = input()
        queue.put(msg)
        tcp_socket.send(msg.encode('ascii'))
        if msg == '/quit' or connections_must_be_closed.is_set():
            print('Conexao encerrada')
            break


def client() -> None:
    try:
        client_socket = initialize_tcp_socket()
        udp_client_socket = initialize_udp_socket(
            address=client_socket.getsockname())
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
            msg_queue = queue.Queue()

            threading.Thread(target=handle_messages, args=[
                             client_socket, udp_client_socket, nickname]).start()
            threading.Thread(target=handle_input, args=[
                             client_socket, msg_queue]).start()
            threading.Thread(target=handle_udp, args=[
                             udp_client_socket, msg_queue]).start()

            while not connections_must_be_closed.is_set():
                pass

        close_sockets(client_socket, udp_client_socket)
    except Exception as exc:
        error_message = f'Houve um erro durante a conexão com o servidor | exc: {str(exc)}'
        print(error_message)
        close_sockets(client_socket, udp_client_socket)


client()
