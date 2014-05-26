#!/usr/bin/python
# FIlename: geoLapse.py

'''
Created on 26 May 2014

@author: rmamba@gmail.com
'''

from decimal import Decimal

import sys
import time
import math
import json

#RaspberryPi: susudo tdo apt-get install python-serial
import serial
	
def writeLog(msg, isDate=True):
	sys.stdout.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
	sys.stdout.flush()

def writeErr(msg, isDate=True):
	sys.stderr.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
	sys.stderr.flush()

def isNoneOrEmptry(val):
	if (val==None) or (val==""):
		return True
	return False

def toDoubleLatLong(latlon, side):
	val = None
	if (isNoneOrEmptry(latlon) or isNoneOrEmptry(side)):
		return None
	try:
		tmp = float(latlon)
		tmp /= 100
		val = math.floor(tmp)
		tmp = (tmp - val) * 100
		val += tmp/60
		tmp -= math.floor(tmp)
		tmp *= 60
		if ((side.upper() == "S") or (side.upper()=="W")):
			val *= -1
	except ValueError:
		writeErr("Can't calculate from {0} side {1}".format(latlon, side))
		val = None
	return val

def toFloat(value):
	val = None
	if isNoneOrEmptry(value):
		return None
	try:
		val = float(value)
	except ValueError:
		writeErr("Can't convert to float: {0}".format(value))
		val = None
	return val

def toInt(value):
	val = None
	if isNoneOrEmptry(value):
		return None
	try:
		val = int(value)
	except ValueError:
		writeErr("Can't convert to int: {0}".format(value))
		val = None
	return val

if __name__ == "__main__":	
	f = open('geoLapse.config', 'r')
	s = f.read()
	__config = json.loads(s)
	f.close()
	
	__device = '/dev/ttyUSB0'
	if 'device' in __config:
		__device = __config['device']
		
	__dir = None
	if 'dir' in __config:
		__dir = __config['dir']
	
	__baud = 4800
	if 'baud' in __config:
		__baud = __config['baud']
	
	__history = None
	if 'history' in __config:
		__history = __config['history']
	
	if __dir == None:
		print "Missing target directory!"
		sys.exit()
	
	try:
		writeLog("Opening port %s" % __device)
		__ser = serial.Serial(port=__device, baudrate=__baud, timeout=1)
		if (__ser != None):
			writeLog("Opened...")
			
	except:
		writeErr("Exception opening port %s" % __device)
		sys.exit()
	
	lapseDelay = 0
	GPS = {}
	
	while 1:
		isChanged = False
		if __ser.inWaiting()>40:
			line = __ser.readline()
			if (__history != None):
				__history.write(line)
			if (line.startswith('$GPGGA')):
				GGA = line.split(',')
				#isChanged = True
			if (line.startswith('$GPRMC')):
				RMC = line.split(',')
				timeGGA = toFloat(GGA[1])
				time = toFloat(RMC[1])
				
				if timeGGA != time:
					print "ERROR in data capture"
				
				knots = toFloat(RMC[7])
				date = toInt(RMC[9])
				
				if not date in GPS:
					GPS[date] = {}
				
				GPS[date][time] = { 
					"Lat": toDoubleLatLong(GGA[2], GGA[3]),
					"Lon": toDoubleLatLong(GGA[4], GGA[5]),
					"Url": { "GoogleMaps": 'https://maps.google.com?q={Lat},{Lon}&z=17'.format(**self.GPS) },
					"Satellites": toInt(GGA[7]),
					"Dilution": toFloat(GGA[8]),
					"Alt": toFloat(GGA[9]),
					"Speed": { 
						"knots": knots,
						"kmh": knots * 1.85200000,
						"mph": knots * 1.15077945,
						"mps": knots * 0.51444444
					},
					"Warning": RMC[2],
					"Direction": toFloat(RMC[8])
				}
				isChanged = True

		if isChanged:
			lapseDelay = lapseDelay + 1
			
		if lapseDelay >= 5:
			lapseDelay = 0
			print GPS
			
			#cmd = ("raspistill -t 250 -tl " + str(tlfreq) + " -o " + dir + "/photo_%04d.jpg")
			#subprocess.call(cmd, shell=True)
			
		time.sleep(.2)