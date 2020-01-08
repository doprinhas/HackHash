from socket import *
import struct
from datetime import datetime


class Client:
    REQ_TIME_OUT = 1
    ANS_TIME_OUT = 15

    DISCOVER_MESSAGE = '1'
    OFFER_MESSAGE = '2'
    REQUEST_MESSAGE = '3'
    ACK_MESSAGE = '4'
    NACK_MESSAGE = '5'
    EMPTY_HASH_MESSAGE = '@*40'
    EMPTY_LENGTH = '0'
    EMPTY_START = 'A'
    EMPTY_END = 'A'
    MESSAGE_FORMAT = '32sc40sc'

    def __init__(self):
        self.client_socket = socket(AF_INET, SOCK_DGRAM)
        self.message_length = 0
        self.hash_code = ''
        self.server_list = []
        self.encrypted_word = ''
        self.team_name = 'f-society' + ' ' * 23

        # serverName = "hostname"

    def connect(self):
        self.hash_code = input('Welcome to' + self.team_name + '. Please enter the hash:')
        self.message_length = input('Please enter the input string length:')
        self.send_broadcast_message()
        self.client_socket.settimeout(1)

        time = datetime.now()
        while (datetime.now() - time).seconds <= self.REQ_TIME_OUT:
            try:
                modified_message, server_address = self.client_socket.recvfrom(586)
                last_field_length = int((len(input) - 74)/2)
                modified_message = struct.unpack(self.MESSAGE_FORMAT + str(last_field_length) + 's' +
                                                 str(last_field_length) + 's', modified_message)
                if modified_message[1].decode("utf-8") == '2':
                    self.server_list.append(server_address[0])
            except:
                pass

        # Send request message
        print(len(self.server_list))
        if len(self.server_list) > 0:
            self.send_request()

        got_answer = False
        time = datetime.now()
        while not got_answer and (datetime.now() - time).seconds <= self.ANS_TIME_OUT:
            try:
                modified_message, server_address = self.client_socket.recvfrom(586)
                last_field_length = int((len(input) - 74) / 2)
                server_answer = (struct.unpack(self.MESSAGE_FORMAT + str(last_field_length) + 's' +
                                               str(last_field_length) + 's', modified_message))
                if server_answer[1].decode("utf-8") == '4':
                    self.encrypted_word = server_answer[4].decode("utf-8")
                    got_answer = True
                if server_answer[1].decode("utf-8") == '5':
                    break
            except:
                pass

        if got_answer:
            print('The input string is ' + self.encrypted_word)
        else:
            print("Timeout - No Answer")

        self.client_socket.close()

    def send_broadcast_message(self):
        self.client_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.client_socket.sendto(
            struct.pack(self.MESSAGE_FORMAT + 'ss', bytes(self.team_name, 'utf-8'), bytes(self.DISCOVER_MESSAGE, 'utf-8'),
                        bytes(self.EMPTY_HASH_MESSAGE, 'utf-8')
                        , bytes(self.EMPTY_LENGTH, 'utf-8'), bytes(self.EMPTY_START, 'utf-8'),
                        bytes(self.EMPTY_END, 'utf-8')), ('255.255.255.255', 3117))

    def send_request(self):

        domains = self.divide_two_domains(int(self.message_length), len(self.server_list))
        i = 0
        for server in self.server_list:
            packed_message = struct.pack(self.MESSAGE_FORMAT + str(len(domains[i])) + 's' + str(len(domains[i])) + 's',
                                         bytes(self.team_name, 'utf-8'), bytes(Client.REQUEST_MESSAGE, 'utf-8'),
                                         bytes(self.hash_code, 'utf-8'), bytes(chr(int(self.message_length)), 'utf-8'),
                                         bytes(domains[i], 'utf-8'),
                                         bytes(bytes(domains[i + 1], 'utf-8')))

            self.client_socket.sendto(packed_message, (server, 3117))
            i = i + 2

    def convert_int_to_string(self, to_convert, length):
        s = ""
        while to_convert > 0:
            c = int(to_convert % 26)
            s = chr(c + 97) + s
            to_convert = int(to_convert / 26)
            length = length - 1
        while length > 0:
            s = 'a' + s
            length = length - 1
        return s

    def convert_string_to_int(self, str):
        char_array = self.split(str)
        num = 0
        for c in char_array:
            if c < 'a' or c > 'z':
                raise RuntimeError("invalid")
            num = num * 26
            num = num + ord(c) - 97
        return num

    def split(self, word):
        return [char for char in word]

    def divide_two_domains(self, len, num_of_servers):
        domains = [None] * num_of_servers * 2
        first = 'a' * len
        last = 'z' * len
        total = self.convert_string_to_int(last)
        per_server = total / num_of_servers
        domains[0] = first
        domains[domains.__len__() - 1] = last
        sum = 0
        j = 1
        while j <= domains.__len__() - 2:
            sum = sum + per_server
            domains[j] = self.convert_int_to_string(sum, len)  # end domain of server
            sum = sum + 1
            domains[j + 1] = self.convert_int_to_string(sum, len)  # start domain of next server
            j = j + 2
        return domains
