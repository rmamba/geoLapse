#!/usr/bin/python
# FIlename: geoLapse.py

'''
Created on 26 May 2014

@author: rmamba@gmail.com
'''

from decimal import Decimal

import os
import sys
import time
import math
import json
import subprocess
import glob

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
	
	#Leave at least 100Mb free
	__minSpace = 100.0
	if 'minSpace' in __config:
		__minSpace = __config['minSpace']
	
	__device = '/dev/ttyUSB0'
	if 'device' in __config:
		__device = __config['device']
		
	__dir = None
	if 'dir' in __config:
		__dir = __config['dir']
	
	__baud = 4800
	if 'baud' in __config:
		__baud = __config['baud']
	
	__width = 800
	if 'width' in __config:
		__width = __config['width']
	__height = 600
	if 'height' in __config:
		__height = __config['height']
	
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
	GGA = None
	RMC = None
	timeRMC = 0
	
	while 1:
		sysTime = int(time.time())
		if __ser.inWaiting()>40:
			line = __ser.readline()
			if (__history != None):
				__history.write(line)
			if (line.startswith('$GPGGA')):
				GGA = line.split(',')
				#isChanged = True
			if (line.startswith('$GPRMC')):
				if GGA == None:
					continue
				RMC = line.split(',')
				timeGGA = int(toFloat(GGA[1]))
				timeRMC = int(toFloat(RMC[1]))
				
				if timeGGA != timeRMC:
					print "ERROR in data capture"
				
				knots = toFloat(RMC[7])
				date = toInt(RMC[9])
				
				Lat = toDoubleLatLong(GGA[2], GGA[3])
				Lon = toDoubleLatLong(GGA[4], GGA[5])
				
				GPS[sysTime] = { 
					"Lat": Lat,
					"Lon": Lon,
					"Url": { "GoogleMaps": 'https://maps.google.com?q={0},{1}&z=17'.format(Lat, Lon) },
					"Satellites": toInt(GGA[7]),
					"Dilution": toFloat(GGA[8]),
					"Alt": toFloat(GGA[9]),
					"Speed": {
						"knots": None,
						"kmh": None,
						"mph": None,
						"mps": None
					},
					"Warning": RMC[2],
					"Direction": toFloat(RMC[8]),
					"DateTime": {
						"time": timeRMC,
						"date": date
					}
				}
				if knots != None:
					GPS[sysTime]["Speed"] = {
						"knots": knots,
						"kmh": knots * 1.85200000,
						"mph": knots * 1.15077945,
						"mps": knots * 0.51444444
					}
				GGA = None
		if sysTime % 5 == 0:
			#check for size
			s = os.statvfs(__dir)
			free = (s.f_bavail * s.f_frsize) / 1048576.0
			if free < __minSpace:
				#delete oldest image
				oldJPEG = sorted(glob.glob(__dir + '/*.jpg'))[0]
				if os.path.isfile(oldJPEG):
					#print "Deleting ", oldJPEG
					os.remove(oldJPEG)
			fileName = "photo-%s.jpg" % sysTime
			cmd = ("raspistill -n -t 100 -w %s -h %s -o %s/%s" % (__width, __height, __dir, fileName) )
			if not os.path.isfile(__dir + '/' + fileName):
				#print cmd
				subprocess.call(cmd, shell=True)
		if (sysTime % 3600 == 0) and (GPS !=None):
			f = open('/var/log/geoLapse-'+str(sysTime)+'.gps', 'w')
			f.write(json.dumps(GPS))
			f.close()
			GPS={}
		time.sleep(.2)
