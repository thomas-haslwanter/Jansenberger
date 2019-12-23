"""
Finds an NGIMU-sensor that is on the same WLAN.
Note that you may have to disable your firewall to allow the sensor-data in!
"""

# author:   Thomas Haslwanter
# date:     Dec-2019

import socket
import time
import osc_decoder


def find_sensor(debug_flag=False):
    # Set up the socket
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

    # Enable broadcasting mode
    server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Set a timeout so the socket does not block
    # indefinitely when trying to receive data.
    server.settimeout(0.2)

    # This bit may not be necessary
    server_address = ('', 8016)     # Note that "localhost" does NOT work!
    server.bind(server_address)

    # Message to send:
    # message = b"your very important message"  # for Computer to Computer
    # message = "/identify\0\0\0".encode()   # for NGIMU
    message = "/wifi/send/ip\0\0,\0\0\00.0.0.0\0".encode()
    if debug_flag:
        print(message)

    while True:
        # server.sendto(message, ('<broadcast>', 37020))
        server.sendto(message, ('255.255.255.255', 9000))   # to all
        # server.sendto(message, ('192.168.1.20', 37020))   # for Computer to Computer
        # server.sendto(message, ('192.168.1.16', 9000))      # for NGIMU

        if debug_flag:
            print("message sent!")
            print('waiting to receive')

        # Receive response
        try:
            data, client_address = server.recvfrom(2048)
        except socket.error:
            pass
        else:
            if debug_flag:
                print(f'received answer from {client_address}')
                for message in osc_decoder.decode(data):
                    print(server.getsockname(), message)
            server.close()
            return client_address

        time.sleep(1)

        
if __name__ == '__main__':
    sensor_address, port = find_sensor(True)
    print(f'IP-address: {sensor_address}')
    print(f'Port: {port}')
    
    