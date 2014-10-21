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

	cnt = 20
	GGA = None
	with open('geoLapse-full.geoJson', 'w') as s:
		with open('geoLapse-light.geoJson', 'w') as l:
			s.write("{\"type\": \"FeatureCollection\", \"spatialReference\":{\"wkid\":102100}, \"features\": [\r\n")
			l.write("{\"type\": \"FeatureCollection\", \"spatialReference\":{\"wkid\":102100}, \"features\": [\r\n")

			for __inputFile in __gpsFiles:
				__outputFile = __inputFile[:-4] + 'geoJson'

				record = int(__inputFile[-15:-5]) - 3600

				linesNMEA = None
				writeLog(__inputFile + ' >> ' + __outputFile)
				with open(__inputFile, 'r') as f:
					rawNMEA = f.read()
					linesNMEA = rawNMEA.split("\r")
				
				if linesNMEA == None:
					writeLog("Error reading NMEA file")
					sys.exit(0)
				
				with open(__outputFile, 'w') as f:
					f.write("{\"type\": \"FeatureCollection\", \"spatialReference\":{\"wkid\":102100}, \"features\": [\r\n")

					for line in linesNMEA:
						if (line.startswith('$GPGGA')):
							GGA = line.split(',')
						if (line.startswith('$GPRMC')):
							if GGA == None:
								continue

							if GGA[6] != '1':
								continue

							RMC = line.split(',')
							timeGGA = int(math.floor(toFloat(GGA[1])))
							timeRMC = int(math.floor(toFloat(RMC[1])))
							
							if timeGGA != timeRMC:
								writeErr("ERROR in data capture")
								writeErr(line)
								#writeErr(oldLine)
							
							knots = toFloat(RMC[7])
							date = toInt(RMC[9])

							Alt = toFloat(GGA[9])
							direction = toFloat(RMC[8])
							DateTime = toInt(RMC[9])
							
							Lat = toDoubleLatLong(GGA[2], GGA[3])
							Lon = toDoubleLatLong(GGA[4], GGA[5])

							kmh = mph = mps = None

							if knots != None:
								kmh = knots * 1.85200000
								mph = knots * 1.15077945
								mps = knots * 0.51444444
							
							
							f.write("\t{\"type\": \"Feature\", \"geometry\": {\"type\": \"Point\", \"coordinates\": [%s, %s]}, \"properties\": {\"timestamp\": %s, \"DateTime\": %s, \"timeGGA\": %s, \"Alt\": %s, \"Speed\": %s, \"Direction\": %s}},\r\n" % (Lon, Lat, record, DateTime, timeGGA, Alt, kmh, direction))
							s.write("\t{\"type\": \"Feature\", \"geometry\": {\"type\": \"Point\", \"coordinates\": [%s, %s]}, \"properties\": {\"timestamp\": %s, \"DateTime\": %s, \"timeGGA\": %s, \"Alt\": %s, \"Speed\": %s, \"Direction\": %s}},\r\n" % (Lon, Lat, record, DateTime, timeGGA, Alt, kmh, direction))
							cnt = cnt - 1
							if cnt == 0:
								l.write("\t{\"type\": \"Feature\", \"geometry\": {\"type\": \"Point\", \"coordinates\": [%s, %s]}, \"properties\": {\"timestamp\": %s, \"DateTime\": %s, \"timeGGA\": %s, \"Alt\": %s, \"Speed\": %s, \"Direction\": %s}},\r\n" % (Lon, Lat, record, DateTime, timeGGA, Alt, kmh, direction))
								cnt = 20
							record = record + 1
							GGA = None
					f.seek(-3, 2)
					f.write("\r\n]}")
			s.seek(-3, 2)
			l.seek(-3, 2)
			s.write("\r\n]}")
			l.write("\r\n]}")
	writeLog("Finished converting GPS data...")
