import struct


def send_message(sock, data):
    length = len(data)
    sock.sendall(struct.pack('!I', length))
    sock.sendall(data)


def recv_message(sock):
    buf_len = recvall(sock, 4)
    length, = struct.unpack('!I', buf_len)
    return recvall(sock, length)


def recvall(sock, count):
    buf = b''
    while count:
        new_buf = sock.recv(count)
        if not new_buf:
            raise Exception('not enough data on socket')
        buf += new_buf
        count -= len(new_buf)
    return buf
