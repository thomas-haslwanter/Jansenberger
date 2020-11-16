import osc_decoder
import socket

udp_ports = [8000, 8039]

udp_sockets = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM) for _ in range(len(udp_ports))]

index = 0
for udp_socket in udp_sockets:
    udp_socket.bind(("", udp_ports[index]))
    index = index + 1
    udp_socket.setblocking(False)

while True:
    for udp_socket in udp_sockets:
        try:
            data, addr = udp_socket.recvfrom(2048)
        except socket.error:
            pass
        else:
            for message in osc_decoder.decode(data):
                print(udp_socket.getsockname(), message)
