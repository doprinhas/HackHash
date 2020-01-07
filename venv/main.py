import struct as st
from socket import *

discover = st.pack('32sc40sc256s256s', bytes('N'*32, encoding='utf-8'), \
                  bytes('1', encoding='utf-8'), bytes(' '*40, encoding='utf-8')\
                  , bytes(chr(0), encoding='utf-8'), bytes(' '*256, encoding='utf-8')\
                  , bytes(' '*256, encoding='utf-8'))


socket = socket(AF_INET, SOCK_DGRAM)
socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
socket.sendto(discover, ('255.255.255.255', 3117))

message, server_address = socket.recvfrom(586)

message = st.unpack('32sc40sc256s256s', message)

for mess in message:
    print(mess.decode('utf-8'))

hash = st.pack('32sc40sc256s256s', bytes('N'*32, encoding='utf-8'), \
                  bytes('3', encoding='utf-8'), bytes('422ab519eac585ef4ab0769be5c019754f95e8dc', encoding='utf-8')\
                  , bytes(chr(6), encoding='utf-8'), bytes('aaaaaa' + ' '*250, encoding='utf-8')\
                  , bytes('zzzzzz' + ' '*250, encoding='utf-8'))
socket.sendto(hash, (server_address[0], 3117))

message, server_address = socket.recvfrom(586)
message = st.unpack('32sc40sc256s256s', message)


for mess in message:
    print(mess.decode('utf-8'))
# mess = socket.recv(600)

