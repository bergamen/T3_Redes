from SocketTCP import SocketTCP as socket
buff_size = 28

server_socket = socket()

address = ('192.168.1.87',8000)

server_socket.bind(address)

new_socket = server_socket.accept()
message = b""
while not new_socket.closed:
    message += new_socket.recv(buff_size)
    print(message.decode())
print(message.decode())