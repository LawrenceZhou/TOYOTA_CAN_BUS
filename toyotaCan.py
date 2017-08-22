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
from OSC import OSCMessage
import numpy as np
import math

#UDP sending part
# UDP socket setting 
import socket
UDP_IP = "192.168.56.1"
UDP_PORT = 5000
MSG = str(time.time())
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MSG, (UDP_IP, UDP_PORT))
print("First trial message sent successfully!")

#VBAP Part
#soundVolume = 1
#l1 = np.array([0, 0])
#l2 = np.array([0, 0])
#l3 = np.array([0, 0])
#l4 = np.array([0, 0])
#g = np.array([0, 0])
p = np.array([0, 0])

#car status
carSpeed = 0
carSteer = 0
carAcceleration = 0
carBrake = 0

#car property
carLength = 2.7
carSteerRatio = 17.6
theta = 0

#sound soure
soundSourceP = np.array([0, 0])
soundSourceV = np.array([0, 0])
soundSourcePLength = 0
soundRadius = 4.8
positionStack = []
initPosition = np.array([0, 0])
positionStack.append(initPosition)


#valve value
STEERSTRAIGHTVALVE = 45
ACCELERATIONVALVE = 15
BRAKEVALVE = 0

#constant parameter
accParam = 0.005
braParam = 0.003
steParam = 0.001
speParam = 0.005

#def calculateG():
#    m = np.asmatrix(np.array([l1, l2]))
#    tempGMatrix = np.dot(np.asmatrix(np.array(p)), m.getI())
#    tempGArray = np.squeeze(np.asarray(tempGMatrix))
#    if tempGArray[0] < 0:
#        tempGArray[0] = 0
#    if tempGArray[1] < 0:
#        tempGArray[1] = 0
#
#    return tempGArray
#
#
#def calculateGScaled(gOriginal):
#    g = np.sqrt(soundVolume) * gOriginal / np.sqrt(gOriginal[0] * gOriginal[0] + gOriginal[1] * gOriginal[1])
#
#
#def selectPair():
#    g12 = calculateG(p, l1, l2)
#    g23 = calculateG(p, l2, l3)
#    g34 = calculateG(p, l3, l4)
#    g41 = calculateG(p, l4, l1)
#
#    listDev = [np.absolute(g12[0] - g12[1]), np.absolute(g23[0] - g23[1]),
#               np.absolute(g34[0] - g34[1]), np.absolute(g41[0] - g41[1])]
#
#    pairSelected = listDev.index(max(listDev))
#    return pairSelected
#
#
#
#def findZone():
#    soundSourcePLength = np.sqrt(soundSourceP[0] * soundSourceP[0] + soundSourceP[1] * soundSourceP[1])
#    if soundSourcePLength < 0.3:
#        return 0
#    else:
#        return 1


def isOnRearVerge(lastPosition):
    soundRadius = 4.8
    if lastPosition[1] > 0:
	return False
    else:
    	soundSourcePLength = np.sqrt(lastPosition[0] * lastPosition[0] + lastPosition[1] * lastPosition[1]) 
   	if soundSourcePLength >= soundRadius:
            return True
        else:
            return False


def isOnFrontVerge(lastPosition):
    soundRadius = 4.8
    if lastPosition[1] < 0:
	return False
    else:
    	soundSourcePLength = np.sqrt(lastPosition[0] * lastPosition[0] + lastPosition[1] * lastPosition[1]) 
   	if soundSourcePLength >= soundRadius:
            return True
        else:
            return False


def isOnVerge(lastPosition):
    soundRadius = 4.8
    soundSourcePLength = np.sqrt(lastPosition[0] * lastPosition[0] + lastPosition[1] * lastPosition[1]) 
    if soundSourcePLength >= soundRadius:
        lastPosition[0] /= soundSourcePLength / soundRadius
        lastPosition[1] /= soundSourcePLength / soundRadius
        return True
    else:
        return False


def calculatePath(carData):
    global carLength
    global carSteerRatio
    global theta
    global soundSourcePLength
    global soundRadius
    global positionStack
    global STEERSTRAIGHTVALVE
    global ACCELERATIONVALVE
    global BRAKEVALVE
    global accParam
    global braParam
    global steParam
    global speParam
    #straight line
    carBrake = carData[0]
    carAcceleration = carData[1]
    #carSpeed = carData[2]
    carSpeed = 3226 #20mph
    carSteer = carData[3]
    lastPosition = positionStack[len(positionStack) - 1]
    newPosition = lastPosition
    if carSteer < STEERSTRAIGHTVALVE and carSteer > -STEERSTRAIGHTVALVE:
        #acceleration situation
        if carAcceleration > ACCELERATIONVALVE:
            if isOnRearVerge(lastPosition):
                #do nothing
                print("On rear verge!")
            else:
                #sound source left behind
                soundSourceV = np.array([0, -carAcceleration * accParam])
                newPosition = lastPosition + soundSourceV
                positionStack.append(newPosition)
        #brake situation
        elif carBrake > BRAKEVALVE:
            if isOnFrontVerge(lastPosition):
                #do nothing
                print("On front verge!")
            else:
                #sound source onrush
                soundSourceV = np.array([0, carBrake * braParam])
                newPosition = lastPosition + soundSourceV
                positionStack.append(newPosition)
        #go back
        else:
            #soundSourceV = np.array([ -soundSourceP[0] / soundSourcePLength, -soundSourceP[1] / soundSourcePLength])
            #soundSourceP = soundSourceP + soundSourceV
            if len(positionStack) > 1:
                newPosition = positionStack[len(positionStack) - 1]
                positionStack.pop()             
            else:
                theta = 0
                newPosition = positionStack[0]
    #turning
    else:
        if isOnVerge(lastPosition):
            #do nothing
            print("On left/right verge!")
	    omega = mphTomps(carSpeed) * math.sin(carSteer / carSteerRatio * math.pi / 180) / carLength * steParam
	    soundSourceV = np.array([ -mphTomps(carSpeed) * math.cos(omega) * speParam, mphTomps(carSpeed) * math.sin(omega) * speParam])
	    newPosition = lastPosition + soundSourceV
            positionStack.append(newPosition)
        else:
            #not fully completed
            #right turn
            if carSteer < 0:
                #wizardOfOz
                #soundSourceV = np.array([ -speed / 20,  speed / 20])
                #soundSourceP = soundSourceP + soundSourceV
                #positionStack.append(soundSourceP)
                #angle
                omega = mphTomps(carSpeed) * math.sin(carSteer / carSteerRatio * math.pi / 180) / carLength
                theta = theta + omega * steParam 
                soundSourceV = np.array([ -mphTomps(carSpeed) * math.cos(theta) * speParam, mphTomps(carSpeed) * math.sin(theta) * speParam])
                newPosition = lastPosition + soundSourceV
                positionStack.append(newPosition)
            #left turn
            else:
                #wizardOfOz
                #soundSourceV = np.array([ speed / 20,  speed / 20])
                #soundSourceP = soundSourceP + soundSourceV
                #positionStack.append(soundSourceP)
                #angle
                omega = mphTomps(carSpeed) * math.sin(carSteer / carSteerRatio * math.pi / 180) / carLength
                theta = theta + omega * steParam 
                soundSourceV = np.array([ mphTomps(carSpeed) * math.cos(theta) * speParam, -mphTomps(carSpeed) * math.sin(theta) * speParam])
                newPosition = lastPosition + soundSourceV
                positionStack.append(newPosition)

    #print(newPosition)
    return newPosition


def realToVBAP(s):
    soundSourcePLength = 4.8
    lp = np.array([s[0] / soundSourcePLength, s[1] / soundSourcePLength])
    return lp


def mphTomps(mph):
    return mph * 0.0062 * 1609 / 3600


def sendPosition(positionX, positionY):
    MSG_ = OSCMessage('/position')
    MSG_ += positionX
    MSG_ += positionY
    print(MSG_)
    binary = MSG_.getBinary()
    sock.sendto(binary, (UDP_IP, UDP_PORT))


cb = 0
csp = 0
ca = 0
cst = 0
def processMsg(msg):
    global cb
    global csp
    global ca
    global cst
    if msg.arbitration_id == 0x0224:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec
        cb = (int(data_[10:12], 16) + int(data_[8:10], 16) * 256) / 15.56

    if msg.arbitration_id == 0x0245: 
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec  
        ca= int(int(data_[4:6], 16) / 2)

    if msg.arbitration_id == 0x00B4:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec
        csp = int(data_[10:15], 16)
 
    if msg.arbitration_id == 0x0025:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec  
        auto_steer = int(data_[0:4], 16) 
        #CounterClockwise from 0 to 343
        if auto_steer < 344: 
            cst = auto_steer
        #Clockwise from 1 to 342
        else:
            auto_steer = auto_steer - 4096
            cst = auto_steer

    return[cb, ca, csp, cst]



def mainProcess(msg):
    carData = processMsg(msg)
    soundSourcePos = calculatePath(carData)
    vectorPos = realToVBAP(soundSourcePos)
    sendPosition(vectorPos[0], vectorPos[1])


#UDP sending function
def send_udp(msg):
    if msg.arbitration_id == 0x0224:
        #send_brake(msg)
	msg = msg
    if msg.arbitration_id == 0x00B4:
        #send_speed(msg)
	msg = msg
    if msg.arbitration_id == 0x0245:   #new 03/01
        #send_accel(msg)   #new 03/01
	msg = msg
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
    
    MSG_ = OSCMessage('/steer')
    #CounterClockwise from 0 to 343  #new 03/01
    if auto_steer < 344:   #new 03/01
        MSG_ += 1 
        MSG_ += auto_steer  #new 03/01
    #Clockwise from 1 to 342   #new 03/01
    else:
        auto_steer = 4096 - auto_steer
        MSG_ += 0
        MSG_ += auto_steer
    print(MSG_)   #new 03/01
    binary = MSG_.getBinary()
    sock.sendto(binary, (UDP_IP, UDP_PORT))   #new 03/01  
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
        #send_udp(msg)
        mainProcess(msg)

         

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        bus.shutdown()
