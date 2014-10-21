#!/usr/bin/python
# FIlename: nmea2csv.py

'''
Created on 29 Aug 2014

@author: rmamba@gmail.com
'''

import os
import sys
import json
import time
import glob
import math

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

	__inputDir = None
	__inputFile = None
	__outputFile = None
	__separate = ','

	if len(sys.argv) == 2:
		__inputDir = sys.argv[1]
	else:
		writeLog("Need input file...")
		sys.exit(0)

	if __inputDir == '.':
		__gpsFiles = glob.glob('*.nmea')
	else:
		__gpsFiles = glob.glob(__inputDir + '/*.nmea')

	with open('geoLapse-full.gps', 'w') as s:
		for __inputFile in __gpsFiles:
			__outputFile = __inputFile[:-4] + 'gps'
			linesNMEA = None
			writeLog(__inputFile + ' >> ' + __outputFile)
			with open(__inputFile, 'r') as f:
				rawNMEA = f.read()
				linesNMEA = rawNMEA.split("\r")
			
			if linesNMEA == None:
				writeLog("Error reading NMEA file")
				sys.exit(0)
			
			with open(__outputFile, 'w') as f:
				GGA = None
				RMC = None
				GPS = {}
				for line in linesNMEA:
					print line
					if (line.startswith('$GPGGA')):
						GGA = line.split(',')
					if (line.startswith('$GPRMC')):
						if GGA == None:
							continue
						RMC = line.split(',')
						timeGGA = int(math.floor(toFloat(GGA[1])))
						timeRMC = int(math.floor(toFloat(RMC[1])))
						
						if timeGGA != timeRMC:
							writeErr("ERROR in data capture")
							writeErr(line)
							writeErr(oldLine)
						
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
				f.write(json.dumps(GPS))
				s.write(json.dumps(GPS))

	writeLog("Finished converting GPS data...")
