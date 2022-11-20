import threading
import socket


host = '127.0.0.1'
port = 55556

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

clients = []
clients_addresses = []
nicknames = []
clients_ports = []


def broadcast(message):
    for client in clients:
        client.send(message)


def handle(client):
    while True:
        try:
            message = client.recv(1024)

            # cliente encerrou a conexão -> removendo o cliente do servidor
            if message.decode('ascii') == '/quit':
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                clients_address = clients_addresses[index]
                clients_port = clients_ports[index]

                print(f'{nickname} disconnected')

                nicknames.remove(nickname)
                clients_addresses.remove(clients_address)
                clients_ports.remove(clients_port)
                

                broadcast(f'{nickname} left the chat'.encode('ascii'))

                
                # atualizar a tabela e fazer o broadcast desta
                tabela = 'NICKNAME             ADDRESS             PORT\n'

                for i in range(len(clients)):
                        tabela = tabela + f'{nicknames[i]}              {clients_addresses[i]}              {clients_ports[i]}\n'
                    

                broadcast(tabela.encode('ascii'))
                
                break

        except:
            # erro na conexão de um cliente -> encerra a conexão
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname = nicknames[index]
            clients_address = clients_addresses[index]
            clients_port = clients_ports[index]

            print(f'{nickname} disconnected')

            nicknames.remove(nickname)
            clients_addresses.remove(clients_address)
            clients_ports.remove(clients_port)
            

            broadcast(f'{nickname} left the chat'.encode('ascii'))

            

            tabela = 'NICKNAME             ADDRESS             PORT\n'

            for i in range(len(clients)):
                    tabela = tabela + f'{nicknames[i]}              {clients_addresses[i]}              {clients_ports[i]}\n'
                

            broadcast(tabela.encode('ascii'))
            
            break

def receive():
    while True:
        client, address = server.accept()
        client_port = address[1]
        client_address = address[0]

        
        print(f'Connected to {str(address)}')


        # loop para verificar se já existe o nome de usuário cadastrado
        while True:
            client.send('NICK'.encode('ascii'))
            nickname = client.recv(1024).decode('ascii')
            if nickname in nicknames:
                client.send('User invalid'.encode('ascii'))
            else:
                break

        print(f'Nickname of the client is {nickname}')

        nicknames.append(nickname)
        clients.append(client)
        clients_addresses.append(client_address)
        clients_ports.append(client_port)
        

        # gerar a tabela com os usuários cadastrados
        tabela = 'NICKNAME             ADDRESS             PORT\n'

        for i in range(len(clients)):
                tabela = tabela + f'{nicknames[i]}              {clients_addresses[i]}              {clients_ports[i]}\n'
            
        # broadcast da tabela para todos os usuários
        broadcast(tabela.encode('ascii'))
        
        broadcast(f'{nickname} joined the chat'.encode('ascii'))
        client.send('\nConnected to the server'.encode('ascii'))

        thread = threading.Thread(target= handle, args=(client,))
        thread.start()

print('Server listening')
receive()