from socket_con_perdida import Sock
import random
import socket

SYN = 1
ACK = 2
FIN = 4

TIMER = 1

class Segment:
    def __init__(self,head=0,sequence=0,body=b""):
        self.head: int = head
        self.sequence: int = sequence
        self.body: bytes = body
    def __bytes__(self):
        return self.head.to_bytes(1) + self.sequence.to_bytes(3) + self.body

class SocketTCP:

    def __init__(self):
        self.socket_tcp = Sock(socket.AF_INET,socket.SOCK_DGRAM)
        self.sequence = 0
        self.buff_size = 16
        self.address = None

        self.init_message = None
        self.last_message = None

        self.length = 0

        self.closed = False

    @staticmethod
    def parse_segment(segment:bytes) -> Segment:
        if len(segment) > 4:
            body = segment[4:]
        else:
            body = b""
        print(segment[0])
        return Segment(segment[0],int.from_bytes(segment[1:4]),body)
    
    @staticmethod
    def create_segment(data:Segment) -> bytes:
        return bytes(data)

    def bind(self,address = ("",0)):
        self.socket_tcp.bind(address)

    def connect(self,address):

        self.sequence = random.randint(0,100)

        data = Segment(SYN,self.sequence)
        resp = None
        while True:
            self.socket_tcp.sendto(self.create_segment(data),address)
            self.socket_tcp.settimeout(TIMER)
            try:
                accept, self.address = self.socket_tcp.recvfrom(4+self.buff_size)
                resp = self.parse_segment(accept)
                if resp.head == SYN + ACK and resp.sequence >= self.sequence:
                    break
            except socket.timeout:
                continue
        

        self.sequence = resp.sequence + 1
        resp.sequence = self.sequence

        resp.head = ACK

        self.socket_tcp.sendto(self.create_segment(resp),self.address)
        print(f"Mi direccion {self.socket_tcp.getsockname()}")
        print(f"Direccion de comunicacion {self.address}")

    def accept(self):
        connect,address = self.socket_tcp.recvfrom(4+self.buff_size)
        connect_parsed = self.parse_segment(connect)
        if connect_parsed.head != SYN:
            return
        new_sockect = SocketTCP()
        new_sockect.sequence = connect_parsed.sequence + 1
        connect_parsed.sequence = new_sockect.sequence
        connect_parsed.head = SYN + ACK
        new_sockect.address = address
        while True:
            new_sockect.socket_tcp.sendto(self.create_segment(connect_parsed),new_sockect.address)
            new_sockect.socket_tcp.settimeout(TIMER)
            try:
                last_ack, _ = new_sockect.socket_tcp.recvfrom(4+self.buff_size)
                break
            except socket.timeout:
                continue
        last_ack_parsed = self.parse_segment(last_ack)

        if last_ack_parsed.head != ACK:
            new_sockect.init_message = last_ack_parsed

        print(f"Mi direccion {self.socket_tcp.getsockname()}")
        print(f"Direccion de comunicacion {new_sockect.address}")
        return new_sockect,new_sockect.socket_tcp.getsockname()


    def send(self,message:bytes):
        length = len(message)
        data = Segment(0,self.sequence,length.to_bytes(16))
        while len(message) > 0:
            print("Send: mandando info")
            self.socket_tcp.sendto(self.create_segment(data),self.address)
            try:
                self.socket_tcp.settimeout(TIMER)
                print("Send: Esperando confirmacion")
                response, _ = self.socket_tcp.recvfrom(4+self.buff_size)
                response_parsed = self.parse_segment(response)
                if response_parsed.head == ACK and response_parsed.sequence > self.sequence:
                    print("Send: Mensaje de confirmacion recivido")
                    data_used = int.from_bytes(response_parsed.body)

                    print(f"Send: bytes usados {data_used}")

                    message = message[data_used:]

                    self.sequence = response_parsed.sequence

                    data = Segment(0,self.sequence,message[:min(self.buff_size,len(message))])

                else:
                    print("Send: Confirmacion errornea")
                    continue
            except socket.timeout:
                print("Send: Timer excedido")
                continue
        

    def recv(self,buff_size:int) -> bytes:
        self.socket_tcp.settimeout(None)
        if self.closed:
            return b""

        total_message = b""
        message_parsed = None

        while self.length <= 0:
            if self.init_message != None:
                message_parsed = self.init_message
                self.init_message = None
            else:
                message,_ = self.socket_tcp.recvfrom(4+self.buff_size)
                message_parsed = self.parse_segment(message)

            if message_parsed.sequence < self.sequence:
                self.socket_tcp.sendto(self.last_message,self.address)
                continue

            if message_parsed.head == FIN:
                print("Recv: Cerrado")
                self.recv_close()
                return b""
            
            self.length = int.from_bytes(message_parsed.body)
            print(f"Recv: Seteando largo {self.length}")
            self.sequence += 16
            data = Segment(ACK,self.sequence,int(0).to_bytes(self.buff_size))
            self.last_message = self.create_segment(data)
            self.socket_tcp.sendto(self.last_message,self.address)
        while len(total_message) < min(buff_size,self.length):
            print("Solicitando informacion")
            message, _ = self.socket_tcp.recvfrom(4+self.buff_size)
            message_parsed = self.parse_segment(message)
            if message_parsed.sequence < self.sequence:
                print("Recv: Mensaje ya recibido")
                self.socket_tcp.sendto(self.last_message,self.address)
                continue
            cut = min(buff_size - len(total_message),self.buff_size)
            total_message += message_parsed.body[:cut]
            print(total_message.decode())
            self.sequence = message_parsed.sequence + cut
            data = Segment(ACK,self.sequence,cut.to_bytes(16))
            self.last_message = self.create_segment(data)
            self.socket_tcp.sendto(self.last_message,self.address)
        self.length -= buff_size
        return total_message

    def close(self):
        print("Entrando a close")
        end_message = Segment(FIN,self.sequence,b"")
        while True:
            self.socket_tcp.sendto(self.create_segment(end_message),self.address)
            try:
                self.socket_tcp.settimeout(TIMER)
                resp, _= self.socket_tcp.recvfrom(4+self.buff_size)
                if self.parse_segment(resp).head == FIN + ACK:
                    self.sequence = self.parse_segment(resp).sequence
                    break
                continue
            except socket.timeout:
                continue
        self.sequence += 1
        for i in range(3):
            last_ack = Segment(ACK,self.sequence,b"")
            self.socket_tcp.sendto(self.create_segment(last_ack),self.address)
            self.socket_tcp.settimeout(TIMER)
            try:
                self.socket_tcp.recvfrom(4+self.buff_size)
            except socket.timeout:
                continue
        self.closed = True

    def recv_close(self):
        print("Cerrando")
        close = False
        self.sequence += 1
        while not close:
            data = Segment(ACK+FIN,self.sequence,b"")
            self.socket_tcp.sendto(self.create_segment(data),self.address)
            for i in range(3):
                try:
                    self.socket_tcp.settimeout(TIMER)
                    resp, _ = self.socket_tcp.recvfrom(4+self.buff_size)
                    resp_parsed = self.parse_segment(resp)
                    if resp_parsed.head == FIN:
                        break
                    elif resp_parsed.head == ACK:
                        close = True
                        break
                except socket.timeout:
                    continue
        self.closed = True