import array
import re
import socket
import struct
import threading

from hashlib import sha1
from base64 import b64encode


SEC_KEY = re.compile(r'Sec-WebSocket-Key: (?P<key>.*)\r\n', re.IGNORECASE)

HOST = ''
PORT = 8002
CHUNKSZ = 2048
MAGIC_STRING = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

client_pool = set()
ID = 1


class WebSocketConnection(object):

    def __init__(self, sock):
        self.id = ID
        self.frame = None
        self.socket = sock

    def handshake(self):
        data = self.socket.recv(CHUNKSZ)
        try:
            search = SEC_KEY.search(data)
            key = search.groupdict()['key']
        except KeyError:
            return False
        hash = sha1()
        hash.update(key + MAGIC_STRING)
        accept = b64encode(hash.digest())
        # construct the response
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: ' + accept + '\r\n\r\n'
        # send it
        self.socket.send(response)
        # the client should send the name of the user
        self.username = self.get_message()
        self.sendall(self.username + ' has connected.', include_self=True)


    def get_message(self):
        self.frame = Frame(self.socket.recv(2))
        if not self.frame.data:
            return
        mask = None
        if self.frame.payload_sz == 126:
            data = self.socket.recv(2)
            self.frame.payload_sz = struct.unpack('!H', data)[0]
        elif self.frame.payload_sz == 127:
            # client has hacked the client code,
            # just play it safe and end the connection
            return
            # data = self.socket.recv(8)
            # self.frame.payload_sz = struct.unpack('!Q', data)[0]
        if self.frame.has_mask:
            mask = self.socket.recv(4)
        data = self.socket.recv(self.frame.payload_sz)
        message = self.handle_mask(mask, data)
        return message

    def serve(self):
        while True:
            message = self.get_message()

            if message is None or message == '\x03\xE9':
                self.quit()
                break
            message = self.username + ': ' + message
            print message
            # send the same frame received to all other clients
            self.sendall(message, include_self=True)
        print "%s has quit." % self.username

    def quit(self):
        self.sendall(self.username + ' has quit.')
        client_pool.remove(self)
        self.socket.close()

    def create_frame(self, message):
        sz = len(message)
        fin = 0x80
        opcode = 0x01
        values = [fin|opcode]
        fmt_str = 'BB'
        if 125 < sz <= 2**16:
            # 126 says to check the next 2 bytes for the payload sz
            values.append(126)
            fmt_str += 'H'
        elif sz > 2**16:
            # this shouldn't happen because I don't want to support that
            # much data in a simple chat client
            return
        # the server doesn't need to send a MASK bit, so it's ignored as a 0 value
        # add the payload sz
        values.append(sz)
        # to add a character pointer, it requires a size
        fmt_str += str(sz) + 's'
        values.append(message.encode('utf-8'))
        return struct.pack(fmt_str, *values)


    def send(self, data):
        self.socket.send(data)

    def sendall(self, message, include_self=False):
        frame = self.create_frame(message)
        for client in client_pool:
            if include_self or client is not self:
                client.send(frame)

    def handle_mask(self, mask, data):
        if mask is None:
            return data
        mask = array.array('B', mask)
        data = array.array('B', data)
        for idx, old_byte in enumerate(data):
            data[idx] = old_byte ^ mask[idx % 4]
        return data.tostring()


class Frame(object):
    """
    WebSocket Frame Reference

         0                   1                   2                   3
         0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
        +-+-+-+-+-------+-+-------------+-------------------------------+
        |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
        |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
        |N|V|V|V|       |S|             |   (if payload len==126/127)   |
        | |1|2|3|       |K|             |                               |
        +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
        |     Extended payload length continued, if payload len == 127  |
        + - - - - - - - - - - - - - - - +-------------------------------+
        |                               |Masking-key, if MASK set to 1  |
        +-------------------------------+-------------------------------+
        | Masking-key (continued)       |          Payload Data         |
        +-------------------------------- - - - - - - - - - - - - - - - +
        :                     Payload Data continued ...                :
        + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
        |                     Payload Data continued ...                |
        +---------------------------------------------------------------+
    """
    def __init__(self, data):
        self.data = data
        if data:
            unpacked = struct.unpack('BB', data)
            self.fin = unpacked[0] & 0x80
            self.opcode = unpacked[0] & 0x0f
            self.payload_sz = unpacked[1] & 0x7f
            self.has_mask = bool(unpacked[1] & 0x80)


def handle_new_client(sock):
    global ID
    # import sys
    # sys.path.append(
    #     r'C:\Program Files (x86)\JetBrains\PyCharm 3.0.2\helpers\pydev\pydevd.py')
    # sys.path.append(
    #     r'C:\Program Files (x86)\JetBrains\PyCharm 3.0.2\pycharm-debug.egg')
    # import pydevd
    #
    # pydevd.settrace('localhost', port=9090, stdoutToServer=True,
    #                 stderrToServer=True)
    client = WebSocketConnection(sock)
    ID += 1
    client_pool.add(client)
    try:
        client.handshake()
        client.serve()
    except Exception as e:
        print e
        client.quit()


def serve():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)
    print 'Listening on', HOST, PORT
    while True:
        sock, addr = s.accept()
        if len(client_pool) < 10:
            print 'Client %s has connected:' % ID, addr
            t = threading.Thread(target=handle_new_client, args=(sock,))
            t.daemon = False
            t.start()

TEST_HEADER = """GET / HTTP/1.1
Upgrade: websocket\r\n
Connection: Upgrade\r\n
Host: localhost:8002\r\n
Origin: https://developer.mozilla.org\r\n
Pragma: no-cache\r\n
Cache-Control: no-cache\r\n
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n
Sec-WebSocket-Version: 13\r\n
Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits,\r\n
x-webkit-deflate-frame\r\n
User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML,\r\n
like Gecko) Chrome/33.0.1750.154 Safari/537.36\r\n\r\n"""

if __name__ == '__main__':
    serve()
