#UDP sending part
# UDP socket setting 
import socket
UDP_IP = "192.168.56.1"
UDP_PORT = 8051
MSG = "HELLO UNITY! CAN YOU HEAR ME?"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MSG, (UDP_IP, UDP_PORT))
print("First trial message sent successfully!")


