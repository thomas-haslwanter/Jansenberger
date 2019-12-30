"""
Routines to interact with an NGIMU-sensor (from XIO technologies)

Questions:
    - How to set the sample rate of the sensor via WLAN?
    - Is "2048" the pre-defined packet length?
    - socket.bind( ("", 0) ) does not work; so how do I know if I should bind to 8015 or
      8016, these two being the only addresses that the NGIMU GUI indicates?

To be done:
    - interaction with multiple sensors
"""

# author:   Thomas Haslwanter & Seb Madgewick
# date:     Dec-2019

import socket
import time
import math
import struct


class Sensor():
    """Routines to interact with an NGIMU-sensor (from XIO technologies)"""


    def __init__(self, timeout=5, debug_flag=False):
        """Tries to establish a connection with an NGIMU on the current WLAN.
        If successful it sets the NGIMU_address (IP_address, port). Otherwise,
        this address is set to (-1, -1)

        When successful, this method sets the following parameters:
        self.packetsize
        self.address
        self.socket
        self.messages

        Note: you may have to disable your firewall to allow the sensor-data in!

        Parameters
        -----=----
        timeout : scalar
                If no sensor can be found at timeout [sec], the initialization is
                terminated, and the socket set to (-1, -1)
        debug_flag : boolean
                   "True" prints out  information while establishing the connection

        """


        # Set up the socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        # Enable broadcasting mode
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Set a timeout so the socket does not block
        # indefinitely when trying to receive data.
        self.socket.settimeout(0.2)

        # alternatively:
        # self.socket.setblocking(False)  # equivalent to self.socket.settimeout(0.0)

        # This bit may not be necessary
        # "localhost" does NOT work! And "0" binds [should bind ???] to an open port
        #address = ('', 0)
        address = ('', 8015)
        self.socket.bind(address)

        # Determined by the NGIMU-protocol?
        self.packetsize = 2048 
        self.messages = []

        # Message to identify NGIMU:
        identify = "/wifi/send/ip\0\0,\0\0\00.0.0.0\0".encode()
        if debug_flag:
            print(identify)
            
        # for debugging
        if timeout == None:
            return

        timer = 0
        while timer < timeout:
            self.socket.sendto(identify, ('255.255.255.255', 9000))   # to all

            if debug_flag:
                print("message sent!")
                print('waiting to receive')

            # Receive response
            try:
                data, client_address = self.socket.recvfrom(self.packetsize)
            except socket.error:
                pass
            else:
                self._process_packet(data)
                if debug_flag:
                    print(f'received answer from {client_address}')
                    for message in self.messages:
                        print(self.socket.getsockname(), message)
                break

            print(f'{timer}/{timeout}')
            time.sleep(1)
            timer += 1

        if timer < timeout:
            self.address =  client_address  # (IP_address, port)
            return
        else:   # timeout
            self.address = (-1, -1)
            print('Could not find any NGIMU-sensor!')


    def close(self):
        """Close the current connection to the NGIMU sensor"""
        self.socket.close()


    def get_data(self, selection):
        """Get the data from the NGIMU

        Parameters
        ----------
        selection : string
                    Must be one of the following:
                    * data : all measurement data (10,)
                    * gyr  : gyroscope [deg/s] (3,)
                    * acc  : accelerometer [g] (3,)
                    * mag  : magnetic field [uT] (3,)
                    * bar  : barometer [hPa] (1,)
                    * quat : quaternions (4,)
        Returns
        -------
        data : ndarray
               Row-vector, shape as indicated under "Parameters"
        """

        received = False
        
        while not received:
            try:
                UDP_data, addr = self.socket.recvfrom(self.packetsize)
            except socket.timeout:
                print('socket timed out!')

                # self.socket.close()
                # self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                # self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                # self.socket.settimeout(0.2)
                # address = ('', 8015)
                # self.socket.bind(address)
                # self.packetsize = 2048 
                # self.messages = []

                # self.socket.close()
                # self.socket.bind(address)

                data = None
                received = True
            except socket.error:
                print('Other socket error.')
                pass
            else:
                self.messages = []
                received = True
                self._process_packet(UDP_data)
                
                # from '/sensors'
                if selection == 'data':
                    data = self.messages[0][2:]                   
                elif selection == 'gyr':
                    data = self.messages[0][2:5]                   
                elif selection == 'acc':
                    data = self.messages[0][5:8]                   
                elif selection == 'mag':
                    data = self.messages[0][8:11]                   
                elif selection == 'bar':
                    data = self.messages[0][-1:]                   
                elif selection == 'quat':
                    # from '/quaternion'
                    data = self.messages[1][2:]                   
                else:
                    raise TypeError(f'Do not know selection type {selection}')

        return data


    def _process_packet(self, data, timestamp=-1):
        """Converts the hexadecimal sensor-message into sensor/quaternion signals.
        Used by "get_data".
        - First splits the overall (binary) message (="bundle") into two separate
            bundles (signals & quaternions), using "_process_bundle"
        - Then converts each of these two (binary) bundles into messages,
          again using "_process_bundle"
        - And finally takes these ASCII strings (="message"), and groups them into
          messages (with "_process_message") with timestamps

        Parameters
        ----------
        data : str
            binary or ASCII string, containing the NGIMU-message

        """

        if data[0] == 35:  # if packet is a bundle ("#" = ASCII 35)
            timetag, contents = self._process_bundle(data)
            # convert to seconds since January 1, 1900.
            # See https://en.wikipedia.org/wiki/Network_Time_Protocol#Timestamps
            timestamp = timetag / pow(2, 32) 

            for content in contents:
                self._process_packet(content, timestamp)  # call recursively

        if data[0] == 47:  # if packet is a message ("#" = ASCII 47)
            message = self._process_message(data)
            if timestamp != -1:
                message[0] = timestamp
            self.messages.append(message)

        return


    def _process_bundle(self, data):
        """Processes hexadecimal data from the NGIMU"""
        
        timetag = int.from_bytes(data[8:16], byteorder='big')  # timetag is uint64 starting at index 8
        elements = data[16:]  # all remaining bytes are contiguous bundle elements
        contents = []
        while len(elements) > 0:
            size = int.from_bytes(elements[0:4], byteorder='big')  # element size is uint32 starting at index 0
            contents.append(elements[4: (size + 4)])  # follow size number of bytes are OSC contents
            elements = elements[(size + 4):]  # skip to next element
        return timetag, contents


    def _process_message(self, data):
        """Groups ASCII-strings into corresponding values"""
        
        message = [-1, data[0:data.index(0)].decode("utf-8")]  # timestamp = -1, get address as string up to "\0"
        remaining = data[data.index(44):]  # type tags and arguments start at ","
        type_tags = remaining[0:(remaining.index(0) + 1)].decode("utf-8")  # type tags end at "\0"
        arguments = remaining[(4 * math.ceil(len(type_tags) / 4)):]  # account for trailing "\0" characters
        
        for type_tag in type_tags:
            if type_tag == ",":  # first character of type tag string
                continue
            elif type_tag == "i":  # argument is uint32
                message.append(int.from_bytes(arguments[0:4], byteorder='big'))
                arguments = arguments[4:]
            elif type_tag == "f":  # argument is float
                float_bytes = bytearray(arguments[0:4])
                float_bytes.reverse()
                message.append(struct.unpack('f', float_bytes)[0])
                arguments = arguments[4:]
            elif type_tag == "\x00":  # last character of type tag string
                continue
            elif type_tag == "s" or type_tag == "S":  # argument is string
                message.append(arguments[0:arguments.index(0)].decode("utf-8"))
                # account for trailing "\0" characters
                arguments = arguments[(4 * math.ceil((len(message[-1]) + 1) / 4)):] 
            elif type_tag == "b":  # argument is blob
                size = int.from_bytes(arguments[0:4], byteorder='big')
                message.append(arguments[4:(4 + size)])
                arguments = arguments[4 + (4 * math.ceil(size / 4)):]  # account for trailing "\0" characters
            elif type_tag == "T":  # argument is True
                message.append(True)
            elif type_tag == "F":  # argument is False
                message.append(False)
            else:
                print("Argument type not supported.", type_tag)
                break
            
        return message

        
if __name__ == '__main__':
    """
    sensor = Sensor(debug_flag=False)
    sensor.close()
    print(sensor.address[1])    
    """
    
    sensor = Sensor(debug_flag=True)
    print(f'IP-address: {sensor.address[0]}')
    print(f'Port: {sensor.address[1]}')
    
    for ii in range(10):
        measurement = sensor.get_data('acc')
        print(ii, measurement)
        time.sleep(0.5)
    
    """
    import pickle
    data_file = 'message.bin'
    ngimu_data = pickle.load(open(data_file, 'rb'))
    
    my_sensor = Sensor(timeout=None)
    my_sensor._process_packet(ngimu_data)
    for message in my_sensor.messages:
        print(message)
    
    """
    
