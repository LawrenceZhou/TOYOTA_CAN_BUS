#!/usr/bin/env python
"""
toyotaCAN.py reads data through CAN Bus.
2016-12-05 Only brake position info will be sent.
UDP communication is added. Temporary communication protocol is used.
message_type(4 bytes)+percent(3 bytes)+timestamp(13 bytes)
"""
from __future__ import print_function
import datetime
import argparse
import time
import binascii 
import can


#UDP sending part
# UDP socket setting 
import socket
UDP_IP = "192.168.56.1"
UDP_PORT = 5000
MSG = str(time.time())
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MSG, (UDP_IP, UDP_PORT))
print("First trial message sent successfully!")


#UDP sending function
def send_udp(msg):
    if msg.arbitration_id == 0x0224:
        send_brake(msg)
    if msg.arbitration_id == 0x00B4:
        send_speed(msg)
    if msg.arbitration_id == 0x0245:   #new 03/01
        send_accel(msg)   #new 03/01
    if msg.arbitration_id == 0x0025:   #new 03/01
        send_steer(msg)   #new 03/01
        
#Send the brake position in percent measurement
def send_brake(msg):
    data_ = binascii.hexlify(msg.data)
    #convert the hex to dec
    brake_position = int(data_[9:12], 16)

    if brake_position > 0:
        #construct the message
        MSG_ = "0224" + str(brake_position).ljust(3) + str(msg.timestamp).ljust(13)
        print(MSG_)
        sock.sendto(MSG_, (UDP_IP, UDP_PORT))

#should modify the send_speed function, to use the non-display speed
def send_speed(msg):
    data_ = binascii.hexlify(msg.data)
    #convert the hex to dec
    auto_speed = int(data_[10:15], 16)

    if auto_speed > 0:
        #construct the message
        MSG_ = "00B4" + str(auto_speed).ljust(5) + str(msg.timestamp).ljust(13)
        print(MSG_)
        sock.sendto(MSG_, (UDP_IP, UDP_PORT))
        
        
def send_accel(msg):    #new 03/01
    data_ = binascii.hexlify(msg.data)  #new 03/01
    #convert the hex to dec    #new 03/01
    auto_accel = int(data_[0:4], 16)   #new 03/01
    #acceleration pedal position, from 128 to 200 
    MSG_ = "0245" + str(auto_accel).ljust(3) + str(msg.timestamp).ljust(13)   #new 03/01
    print(MSG_)   #new 03/01
    sock.sendto(MSG_, (UDP_IP, UDP_PORT))   #new 03/01   

 
def send_steer(msg):    #new 03/01
    data_ = binascii.hexlify(msg.data)  #new 03/01
    #convert the hex to dec    #new 03/01
    auto_steer = int(data_[0:4], 16)   #new 03/01
    
    #CounterClockwise from 0 to 343  #new 03/01
    if auto_steer < 344:   #new 03/01
        MSG_ = "0025" + "1" + str(auto_steer).ljust(3) + str(msg.timestamp).ljust(13)   #new 03/01
    #Clockwise from 1 to 342   #new 03/01
    else:
        auto_steer = 4096 - auto_steer
        MSG_ = "0025" + "0" + str(auto_steer).ljust(3) + str(msg.timestamp).ljust(13)   #new 03/01
    print(MSG_)   #new 03/01
    sock.sendto(MSG_, (UDP_IP, UDP_PORT))   #new 03/01  
#UDP sending part


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Log CAN traffic, printing messages to stdout or to a given file")

    parser.add_argument("-f", "--file_name", dest="log_file",
                        help="""Path and base log filename, extension can be .txt, .csv, .db, .npz""",
                        default=None)

    parser.add_argument("-v", action="count", dest="verbosity",
                        help='''How much information do you want to see at the command line?
                        You can add several of these e.g., -vv is DEBUG''', default=2)

    parser.add_argument('-c', '--channel', help='''Most backend interfaces require some sort of channel.
    For example with the serial interface the channel might be a rfcomm device: /dev/rfcomm0
    Other channel examples are: can0, vcan0''', default=can.rc['channel'])

    parser.add_argument('-i', '--interface', dest="interface", help='''Which backend do you want to use?''',
                        default='kvaser', choices=('kvaser', 'socketcan', 'socketcan_ctypes',
                                                   'socketcan_native', 'pcan', 'serial'))

    parser.add_argument('--filter', help='''Comma separated filters can be specified for the given CAN interface:
        <can_id>:<can_mask> (matches when <received_can_id> & mask == can_id & mask)
        <can_id>~<can_mask> (matches when <received_can_id> & mask != can_id & mask)
    ''', nargs=argparse.REMAINDER, default='')

    results = parser.parse_args()

    verbosity = results.verbosity

    logging_level_name = ['critical', 'error', 'warning', 'info', 'debug', 'subdebug'][min(5, verbosity)]
    can.set_logging_level(logging_level_name)

    can_filters = []
    if len(results.filter) > 0:
        print('we have filter/s', results.filter)
        for filt in results.filter:
            if ':' in filt:
                _ = filt.split(":")
                can_id, can_mask = int(_[0], base=16), int(_[1], base=16)
            elif "~" in filt:
                can_id, can_mask = filt.split("~")
                can_id = int(can_id, base=16) | 0x20000000    # CAN_INV_FILTER
                can_mask = int(can_mask, base=16) & socket.CAN_ERR_FLAG
            can_filters.append({"can_id": can_id, "can_mask": can_mask})

    bus = can.interface.Bus(results.channel, bustype=results.interface, can_filters=can_filters)
    #print('Can Logger (Started on {})\n'.format(datetime.datetime.now()))
    #notifier = can.Notifier(bus, [can.Printer(results.log_file), can.Printer(results.log_file)])
      
    #Sending message through UDP  
    for msg in bus:
        send_udp(msg)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.shutdown()
