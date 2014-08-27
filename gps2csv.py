#!/usr/bin/python
# FIlename: gps2csv.py

'''
Created on 18 Aug 2014

@author: rmamba@gmail.com
'''

import os
import sys
import json
import time
import glob

def writeLog(msg, isDate=True):
	sys.stdout.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
	sys.stdout.flush()

def writeErr(msg, isDate=True):
	sys.stderr.write("%s: %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
	sys.stderr.flush()

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
		__gpsFiles = glob.glob('*.gps')
	else:
		__gpsFiles = glob.glob(__inputDir + '/*.gps')

	cnt = 10
	with open('geoLapse-full.csv', 'w') as s:
		with open('geoLapse-light.csv', 'w') as l:
			s.write("timestamp%s date%s time%s Lat%s Lon%s Alt%s speed%s direction\r\n" % (__separate, __separate, __separate, __separate, __separate, __separate, __separate))
			l.write("timestamp%s date%s time%s Lat%s Lon%s Alt%s speed%s direction\r\n" % (__separate, __separate, __separate, __separate, __separate, __separate, __separate))

			for __inputFile in __gpsFiles:
				__outputFile = __inputFile[:-3] + 'csv'
				dataJson = None
				writeLog(__inputFile + ' >> ' + __outputFile)
				with open(__inputFile, 'r') as f:
					rawJson = f.read()
					dataJson = json.loads(rawJson)
				
				if json == None:
					writeLog("Error reading GPS file")
					sys.exit(0)
				
				with open(__outputFile, 'w') as f:
					f.write("timestamp%s date%s time%s Lat%s Lon%s Alt%s speed%s direction\r\n" % (__separate, __separate, __separate, __separate, __separate, __separate, __separate))

					for record in sorted(dataJson):
						if dataJson[record]['Lat'] != None:
							f.write("%s%s %s%s %s%s %s%s %s%s %s%s %s%s %s\r\n" % (record, __separate, dataJson[record]['DateTime']['date'], __separate, dataJson[record]['DateTime']['time'], __separate, dataJson[record]['Lat'], __separate, dataJson[record]['Lon'], __separate, dataJson[record]['Alt'], __separate, dataJson[record]['Speed']['kmh'], __separate, dataJson[record]['Direction']))
							s.write("%s%s %s%s %s%s %s%s %s%s %s%s %s%s %s\r\n" % (record, __separate, dataJson[record]['DateTime']['date'], __separate, dataJson[record]['DateTime']['time'], __separate, dataJson[record]['Lat'], __separate, dataJson[record]['Lon'], __separate, dataJson[record]['Alt'], __separate, dataJson[record]['Speed']['kmh'], __separate, dataJson[record]['Direction']))
							cnt = cnt - 1
							if cnt == 0:
								l.write("%s%s %s%s %s%s %s%s %s%s %s%s %s%s %s\r\n" % (record, __separate, dataJson[record]['DateTime']['date'], __separate, dataJson[record]['DateTime']['time'], __separate, dataJson[record]['Lat'], __separate, dataJson[record]['Lon'], __separate, dataJson[record]['Alt'], __separate, dataJson[record]['Speed']['kmh'], __separate, dataJson[record]['Direction']))
								cnt = 10

	writeLog("Finished converting GPS data...")
