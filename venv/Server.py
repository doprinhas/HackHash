from multiprocessing import Pool
import asyncio
import hashlib
from datetime import datetime
import struct as st
from socket import *

ANS_TIME_OUT = 10


class Server:
    MESSAGE_FORMAT = '32sc40sc'

    def __init__(self, num_of_processes, listen_port):
        self.server_online = True
        self.semaphore = asyncio.Semaphore(1)
        self.pool = Pool(processes=num_of_processes)
        self.server_port = listen_port
        self.ports = [port for port in range(listen_port + 1, listen_port + num_of_processes + 1)]
        self.current_send_port_index = 0
        self.received_discover = {}

    def listen(self):

        server_socket = socket(AF_INET, SOCK_DGRAM)
        server_socket.bind(('', self.server_port))

        while self.server_online:
            message, client_address = server_socket.recvfrom(586)
            if self.is_discover_message(message, '1'):
                self.received_discover[client_address] = True
            # self.pool.apply_async(func=handle_massage,
            #                       args=[message, client_address, self.get_port_index(),
            #                             client_address in self.received_discover.keys()])
            handle_massage(message, client_address, self.get_port_index(), client_address in self.received_discover.keys())
            if self.is_discover_message(message, '3'):
                del self.received_discover[client_address]

    def is_discover_message(self, input, type):
        if len(input) <= 586:
            return False
        last_field_length = int((len(input) - 74)/2)
        unpacked_message = st.unpack(self.MESSAGE_FORMAT + Str(last_field_length) + 's' + Str(last_field_length) + 's',
                                     input)
        unpacked_message = [mess.decode('utf-8') for mess in unpacked_message]
        if ord(type) == ord(unpacked_message[1]):
            return True
        return False

    def get_port_index(self):
        index = self.current_send_port_index
        self.current_send_port_index += 1
        if self.current_send_port_index == len(self.ports):
            self.current_send_port_index = 0
        return self.ports[index]

    def close(self):
        self.pool.close()
        self.server_online = False


DISCOVER_MESSAGE = '1'
OFFER_MESSAGE = '2'
REQUEST_MESSAGE = '3'
ACK_MESSAGE = '4'
NACK_MESSAGE = '5'

MESSAGE_FORMAT = '32sc40sc'

TYPE_INDEX = 1
HASH_INDEX = 2
STRING_LENGTH_INDEX = 3
START_STRING_INDEX = 4
END_STRING_INDEX = 5


# received_discover = {}

def handle_massage(message, client_address, send_port, is_sent_discover):
    if not is_input_valid(message):
        return send_error(client_address, send_port)

    last_field_length = int((len(input) - 74)/2)

    message_tup = st.unpack(MESSAGE_FORMAT + str(last_field_length) + 's' + str(last_field_length) + 's', message)
    message_tup = [mess.decode('utf-8') for mess in message_tup]

    print(client_address)

    if message_tup[TYPE_INDEX] == DISCOVER_MESSAGE:
        send_offer_to_client(message_tup, client_address, send_port)
    elif message_tup[TYPE_INDEX] == REQUEST_MESSAGE and is_sent_discover:
        search_hash(message_tup, client_address, send_port)
    else:
        send_error(client_address, send_port)


def is_input_valid(input):
    if len(input) > 586:
        return False
    last_field_length = int((len(input) - 74)/2)
    format = MESSAGE_FORMAT + string(last_field_length) + 's' + string(last_field_length) + 's'
    unpacked_message = st.unpack(format, input)
    unpacked_message = [mess.decode('utf-8') for mess in unpacked_message]
    if ord('1') == ord(unpacked_message[1]):
        return True
    if ord('3') != ord(unpacked_message[1]):
        return False
    if not (unpacked_message[2].islower()):
        return False
    length = ord(unpacked_message[3])
    str = unpacked_message[4].replace(' ', '')
    if (not (str.isalpha() and str.islower())) or len(str) != length:
        return False
    str = unpacked_message[5].replace(' ', '')
    if (not (str.isalpha() and str.islower())) or len(str) != length:
        return False
    return True


def get_packed_message(message_format, message_content_string_tup):
    fields_in_bytes = [to_bytes(field) for field in message_content_string_tup]
    packed_message = st.pack(message_format, fields_in_bytes[0], fields_in_bytes[1], fields_in_bytes[2],
                             fields_in_bytes[3], fields_in_bytes[4], fields_in_bytes[5])
    return packed_message


def send_message(to, byte_message, port):
    send_socket = socket(AF_INET, SOCK_DGRAM)
    send_socket.bind(('', port))
    send_socket.sendto(byte_message, to)
    send_socket.close()


def send_error(client_address, port):
    message = 'Invalid Arguments' + ' ' * 64
    send_message(client_address, to_bytes(message), port)


def send_offer_to_client(message_tup, client_address, port):
    message_content = [message_tup[0], OFFER_MESSAGE, ' ' * 40, '0', ' ' * 1, ' ' * 1]
    message = get_packed_message(MESSAGE_FORMAT + 'ss', message_content)
    send_message(client_address, message, port)


def send_ack(ans, message_tup, client_address, port):
    message_content = [message_tup[0], ACK_MESSAGE, ' ' * 40, '0', ans, ' ' * len(ans)]
    message = get_packed_message(MESSAGE_FORMAT + str(len(ans)) + 'ss', message_content)
    send_message(client_address, message, port)


def send_nack(message_tup, client_address, port):
    message_content = [message_tup[0], NACK_MESSAGE, ' ' * 40, '0', ' ' * 1, ' ' * 1]
    message = get_packed_message(MESSAGE_FORMAT + 'ss', message_content)
    send_message(client_address, message, port)


def to_bytes(string):
    return bytes(string, encoding='utf-8')


def search_hash(message_tup, client_address, port):
    hash = str(message_tup[HASH_INDEX])
    end_str = str(message_tup[END_STRING_INDEX]).replace(' ', '')
    end_str = get_next_string(end_str)

    check_str = str(message_tup[START_STRING_INDEX]).replace(' ', '')
    time = datetime.now()
    while check_str != end_str and (datetime.now() - time).seconds <= ANS_TIME_OUT:
        hash_to = hashlib.sha1(to_bytes(check_str)).hexdigest()
        if hash_to == hash:
            return send_ack(check_str, message_tup, client_address, port)
        check_str = get_next_string(check_str)
    send_nack(message_tup, client_address, port)


def get_next_string(string):
    i = -1
    while string[i] == 'z':
        i -= 1
        if i * -1 > len(string):
            return None
    return string[:i] + chr(ord(string[i]) + 1) + 'a' * (-i - 1)
