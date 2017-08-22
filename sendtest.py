import binascii 
import can
import time
import math
from OSC import OSCMessage
import numpy as np

#UDP sending part
# UDP socket setting 
import socket
UDP_IP = "192.168.56.1"
UDP_PORT = 5000
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

#valve value
STEERSTRAIGHTVALVE = 45
ACCELERATIONVALVE = 15
BRAKEVALVE = 15


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


def isOnVerge():
    global soundSourceP
    global soundSourcePLength
    global soundRadius
    soundSourcePLength = np.sqrt(soundSourceP[0] * soundSourceP[0] + soundSourceP[1] * soundSourceP[1]) 
    if soundSourcePLength >= soundRadius:
        return True
    else:
        return False


def calculatePath():
    global carSpeed
    global carSteer
    global carAcceleration
    global carBrake
    global carLength
    global carSteerRatio
    global theta
    global soundSourceP
    global soundSourceV
    global soundSourcePLength
    global soundRadius
    global positionStack
    global STEERSTRAIGHTVALVE
    global ACCELERATIONVALVE
    global BRAKEVALVE
    #straight line
    if carSteer < STEERSTRAIGHTVALVE and carSteer > -STEERSTRAIGHTVALVE:
        #acceleration situation
        if carAcceleration > ACCELERATIONVALVE:
            if isOnVerge():
                #do nothing
                soundSourceP = soundSourceP
            else:
                #sound source left behind
                soundSourceV = np.array([0, -carAcceleration * 0.02])
                soundSourceP = soundSourceP + soundSourceV
                positionStack.append(soundSourceP)
        #brake situation
        elif carBrake > BRAKEVALVE:
            if isOnVerge():
                #do nothing
                soundSourceP = soundSourceP
            else:
                #sound source onrush
                soundSourceV = np.array([0, carBrake * 0.005])
                soundSourceP = soundSourceP + soundSourceV
                positionStack.append(soundSourceP)
        #go back
        else:
            #soundSourceV = np.array([ -soundSourceP[0] / soundSourcePLength, -soundSourceP[1] / soundSourcePLength])
            #soundSourceP = soundSourceP + soundSourceV
            if len(positionStack) > 0 :
                soundSourceP = positionStack.pop()
            else:
                theta = 0
                soundSourceP = np.array([0, 0])
    #turning
    else:
        if isOnVerge():
            #do nothing
            soundSourceP = soundSourceP
        else:
            #not fully completed
            #right turn
            if carSteer < 0:
                #wizardOfOz
                #soundSourceV = np.array([ -speed / 20,  speed / 20])
                #soundSourceP = soundSourceP + soundSourceV
                #positionStack.append(soundSourceP)
                #angle
                #omega = 11 * math.sin(carSteer / carSteerRatio * math.pi / 180) / carLength
		omega = 4 * math.sin(carSteer / carSteerRatio * math.pi / 180)
                theta = theta + omega * 0.01
		#print theta
                soundSourceV = np.array([ -carSpeed * math.cos(theta) * 0.01 * 0.05, carSpeed * math.sin(theta) * 0.01 * 0.05])
                soundSourceP = soundSourceP + soundSourceV
		#print soundSourceP
                positionStack.append(soundSourceP)
            #left turn
            else:
                #wizardOfOz
                #soundSourceV = np.array([ speed / 20,  speed / 20])
                #soundSourceP = soundSourceP + soundSourceV
                #positionStack.append(soundSourceP)
                #angle
                omega = carSpeed * math.sin(carSteer / carSteerRatio * math.pi / 180) / carLength
                theta = theta + omega
                soundSourceV = np.array([ carSpeed * math.cos(theta) * 0.01 * 0.01, -carSpeed * math.sin(theta) * 0.01 * 0.01])
                soundSourceP = soundSourceP + soundSourceV
                positionStack.append(soundSourceP)


def realToVBAP():
    global soundRadius
    global p
    #soundSourcePLength = np.sqrt(soundSourceP[0] * soundSourceP[0] + soundSourceP[1] * soundSourceP[1])
    p = np.array([soundSourceP[0] / soundRadius, soundSourceP[1] / soundRadius])


def sendPosition(positionX, positionY):
    MSG_ = OSCMessage('/position')
    MSG_ += positionX
    MSG_ += positionY
    #print(MSG_)
    binary = MSG_.getBinary()
    sock.sendto(binary, (UDP_IP, UDP_PORT))


def processMsg(msg):
    if msg.arbitration_id == 0x0224:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec
        carBrake = int(data_[9:12], 16)

    if msg.arbitration_id == 0x00B4:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec
        carSpeed = int(data_[10:15], 16)

    if msg.arbitration_id == 0x0245: 
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec  
        carAcceleration = int(data_[0:4], 16) 

    if msg.arbitration_id == 0x0025:
        data_ = binascii.hexlify(msg.data)
        #convert the hex to dec  
        auto_steer = int(data_[0:4], 16) 
        #CounterClockwise from 0 to 343
        if auto_steer < 344: 
            carSteer = auto_steer
        #Clockwise from 1 to 342
        else:
            auto_steer = auto_steer - 4096
            carSteer = auto_steer


def mainProcess():
    global carAcceleration
    global carBrake
    global carSteer
    global carSpeed
    flag = 0
    carSpeed = 25
    count = 0
    count2 = 0
    while(1):
        if flag == 0 and count < 500:
	        count += 1
  	elif flag == 0 and carSteer < -90:
	    if count2 < 1500:
	        count2 += 1
            else:
		flag = 1
   	elif flag == 0:
            carSteer -= 2

        if flag == 1:
	    if carSteer < 0:
                carSteer += 2
	print carSteer
        calculatePath()
        realToVBAP()
        sendPosition(p[0], p[1])
        time.sleep(0.01)


mainProcess()


