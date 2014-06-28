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

import RPi.GPIO as GPIO
	
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

def writePID():
	pid = str(os.getpid())
	with open('/var/run/geoLapse.pid', 'w') as f:
		f.write(pid)

if __name__ == "__main__":
	LED0 = 16
	LED1 = 18
	LED2 = 22
	KEY = 7
	SW = 11
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)
	
	GPIO.setup(LED0, GPIO.OUT)
	GPIO.setup(LED1, GPIO.OUT)
	GPIO.setup(LED2, GPIO.OUT)
	GPIO.setup(KEY, GPIO.IN)
	GPIO.setup(SW, GPIO.IN)
	
	GPIO.output(LED0, 1)
	GPIO.output(LED1, 0)
	GPIO.output(LED2, 0)
	
	#writePID()
	configFile = 'geoLapse.config'
	if len(sys.argv) == 2:
		configFile = sys.argv[1]
	
	with open(configFile, 'r') as f:
		s = f.read()
		__config = json.loads(s)
	
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
	
	__override = False
	if 'override' in __config:
		__override = __config['override']
	
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
	blink = 0
	cntDownReset = 35
	cntDown = cntDownReset
	bRun = True
	bDumpGPS = True
	
	while bRun:
		sysTime = int(time.time())
		if __ser.inWaiting()>40:
			line = __ser.readline()
			if (__history != None):
				__history.write(line)
			if (line.startswith('$GPGGA')):
				GGA = line.split(',')
				if GGA[2]!='':
					GPIO.output(LED1, 1)
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
				GPIO.output(LED1, 0)
		if (sysTime % 5 == 0) and (GPIO.input(7)==1):
			GPIO.output(LED2, 1)
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
			#print cmd
			if (not os.path.isfile(__dir + '/' + fileName)) or (__override == True):
				#print cmd
				subprocess.call(cmd, shell=True)
			GPIO.output(LED2, 0)
		if (sysTime % 3600 == 0) and (GPS !=None):
			with open('/var/log/geoLapse-'+str(sysTime)+'.gps', 'w') as f:
				f.write(json.dumps(GPS))
			GPS={}
		blink = blink + 1
		if blink > 15:
			blink = 0
		GPIO.output(LED0, blink % 2)
		if GPIO.input(11) == 1:
			GPIO.output(LED0, 1)
			if cntDown > 0:
				cntDown = cntDown - 1
				if (cntDown<10) and bDumpGPS:
					bDumpGPS = False
					with open('/var/log/geoLapse-'+str(sysTime)+'.gps', 'w') as f:
						f.write(json.dumps(GPS))
					GPS={}
			else:
				with open('/var/log/geoLapse-'+str(sysTime)+'.gps', 'w') as f:
					f.write(json.dumps(GPS))
				GPS={}
				subprocess.call('sudo shutdown -h now', shell=True)
		else:
			cntDown = cntDownReset
			bDumpGPS = True
		try:
			time.sleep(.2)
		except KeyboardInterrupt:
			print "Saving GPS data..."
			with open('/var/log/geoLapse-'+str(sysTime)+'.gps', 'w') as f:
				f.write(json.dumps(GPS))
			GPS={}
			bRun = False
	print "Ending geoLapse..."
