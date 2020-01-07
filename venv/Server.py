from multiprocessing import Pool
import asyncio
import hashlib
import struct as st
from socket import *

class Server:

    DISCOVER_MESSAGE = '1'
    OFFER_MESSAGE = '2'
    REQUEST_MESSAGE = '3'
    ACK_MESSAGE = '4'
    NACK_MESSAGE = '5'

    MESSAGE_FORMAT = '32sc40sc256s256s'

    TYPE_INDEX = 1
    HASH_INDEX = 2
    STRING_LENGHT_INDEX = 3
    START_STRING_INDEX = 4
    END_STRING_INDEX = 5

    def __init__(self, num_of_thred, listen_port):
        self.server_online = True
        self.semaphore = asyncio.Semaphore(1)
        self.thred_pool = Pool(processes=num_of_thred)
        self.server_port = listen_port
        self.ports = [port for port in range(listen_port+1, listen_port+num_of_thred+1)]
        self.current_send_port_index = 0


    def listen(self):

        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind(('', self.server_port))

        while self.server_online:
            message, client_address = server_socket.recvfrom(586)
            self.handle_massage(message, client_address)


    def handle_massage(self, message, client_address):
        message_tup = st.unpack(self.MESSAGE_FORMAT, message)
        message_tup = [mess.decode('utf-8') for mess in message_tup]
        
        if message_tup[self.TYPE_INDEX] == self.DISCOVER_MESSAGE:
            self.send_offer_to_client(message_tup, client_address)
        elif message_tup[self.TYPE_INDEX] == self.REQUEST_MESSAGE:
            print(self.search_hash(message_tup, client_address))


    def send_error(self, client_address):
        send_socket = socket(AF_INET, SOCK_DGRAM)
        send_socket.bind(('', 3118))
        send_message = b"invalid args"
        send_socket.sendto(send_message, client_address)
        send_socket.close()

    def send_offer_to_client(self, message_tup, client_address):
        send_socket = socket(AF_INET, SOCK_DGRAM)
        send_socket.bind(('', 3118))
        send_message = st.pack(self.MESSAGE_FORMAT, self.to_bytes(message_tup[0]), \
                                self.to_bytes(self.OFFER_MESSAGE),
                                self.to_bytes(' '*40), \
                                self.to_bytes('0'), self.to_bytes(' '*256), self.to_bytes(' '*256))
        send_socket.sendto(send_message, client_address)
        send_socket.close()

    def to_bytes(self, string):
        return bytes(string, encoding='utf-8')

    def search_hash(self, message_tup, client_address):
        hash = str(message_tup[self.HASH_INDEX])
        # binary_hash = ''.join(format(i, 'b') for i in self.to_bytes(hash))
        end_str = self.get_next_string(str(message_tup[self.END_STRING_INDEX]))
        if (end_str != None):
            end_str = end_str.replace(' ', '')

        check_str = str(message_tup[self.START_STRING_INDEX]).replace(' ', '')

        while check_str != end_str:
            hash_to = hashlib.sha1(self.to_bytes(check_str)).hexdigest()
            if (hash_to == hash):
                return self.send_ack(check_str, message_tup, client_address)
            check_str = self.get_next_string(check_str)
        self.send_nack(message_tup, client_address)

    def send_ack(self, ans, message_tup, client_address):
        send_socket = socket(AF_INET, SOCK_DGRAM)
        send_socket.bind(('', 3118))
        send_message = st.pack(self.MESSAGE_FORMAT, self.to_bytes(message_tup[0]), \
                                self.to_bytes(self.ACK_MESSAGE),
                                self.to_bytes(' '*40), \
                                self.to_bytes('0'), self.to_bytes(ans + ' '*(256-len(ans))), self.to_bytes(' '*256))
        send_socket.sendto(send_message, client_address)
        send_socket.close()
        
    def send_nack(self, message_tup, client_address):
        send_socket = socket(AF_INET, SOCK_DGRAM)
        send_socket.bind(('', 3118))
        send_message = st.pack(self.MESSAGE_FORMAT, self.to_bytes(message_tup[0]), \
                                self.to_bytes(self.NACK_MESSAGE),
                                self.to_bytes(' '*40), \
                                self.to_bytes('0'), self.to_bytes(' '*256), self.to_bytes(' '*256))
        send_socket.sendto(send_message, client_address)
        send_socket.close()

    def get_next_string(self, string):
        i = -1
        while string[i] == 'z':
            i -= 1
            if i * -1 > len(string):
                return None
        return string[:i] + chr(ord(string[i]) + 1) + 'a' * (-i -1)

    def get_port_index(self):
        # await self.semaphore.acquire()
        try:
            index = self.current_send_port_index
            self.current_send_port_index += 1
            if (self.current_send_port_index == len(self.ports)):
                self.current_send_port_index = 0
        finally:
            self.lock.release()
        return index

    def close(self):
        self.thred_pool.close()
        self.server_online = False