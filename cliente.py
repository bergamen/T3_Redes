from SocketTCP import SocketTCP as socket
import sys

buff_size = 20

client_socket = socket()

address = (sys.argv[1],int(sys.argv[2]))

client_socket.connect(address)

cont = b''
try:
    while True:
        cont += (input() + "\n").encode()
except EOFError:
    cont = cont[:-1]
    print(cont.decode())

while len(cont) > 0:

    largo = min(buff_size,len(cont))
    trozo = cont[:largo]
    client_socket.send(trozo)
    cont = cont[largo:]

client_socket.close()