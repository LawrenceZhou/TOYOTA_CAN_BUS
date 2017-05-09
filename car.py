import argparse
import random
import time
from OSC import OSCMessage

import socket
UDP_IP = "192.168.56.1"
UDP_PORT = 5000
MSG = OSCMessage('/time')
MSG += str(4.5)
MSG += str(123.0)
binary = MSG.getBinary()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(binary, (UDP_IP, UDP_PORT))
print("First trial message sent successfully!")
