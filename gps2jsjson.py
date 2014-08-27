#!/usr/bin/python
# FIlename: gps2jsjson.py

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

	sPrva = True
	with open('geoLapse-full.js.json', 'w') as s:
		s.write("[")

		for __inputFile in __gpsFiles:
			__outputFile = __inputFile[:-3] + 'js.json'
			dataJson = None
			writeLog(__inputFile + ' >> ' + __outputFile)
			with open(__inputFile, 'r') as f:
				rawJson = f.read()
				dataJson = json.loads(rawJson)
			
			if json == None:
				writeLog("Error reading GPS file")
				sys.exit(0)
			
			fPrva = True
			with open(__outputFile, 'w') as f:
				f.write("[")

				for record in sorted(dataJson):
					if dataJson[record]['Lat'] != None:
						if fPrva:
							f.write("\r\n\t{ \"Timestamp\":%s, \"Date\":\"%s\", \"Time\":\"%s\", \"Lat\":%s, \"Lon\":%s, \"Alt\":%s, \"Speed\":%s, \"Direction\":%s}" % (record, dataJson[record]['DateTime']['date'], dataJson[record]['DateTime']['time'], dataJson[record]['Lat'], dataJson[record]['Lon'], dataJson[record]['Alt'], dataJson[record]['Speed']['kmh'], dataJson[record]['Direction']))
							fPrva = False
						else:
							f.write(",\r\n\t{ \"Timestamp\":%s, \"Date\":\"%s\", \"Time\":\"%s\", \"Lat\":%s, \"Lon\":%s, \"Alt\":%s, \"Speed\":%s, \"Direction\":%s}" % (record, dataJson[record]['DateTime']['date'], dataJson[record]['DateTime']['time'], dataJson[record]['Lat'], dataJson[record]['Lon'], dataJson[record]['Alt'], dataJson[record]['Speed']['kmh'], dataJson[record]['Direction']))

						if sPrva:
							s.write("\r\n\t{ \"Timestamp\":%s, \"Date\":\"%s\", \"Time\":\"%s\", \"Lat\":%s, \"Lon\":%s, \"Alt\":%s, \"Speed\":%s, \"Direction\":%s}" % (record, dataJson[record]['DateTime']['date'], dataJson[record]['DateTime']['time'], dataJson[record]['Lat'], dataJson[record]['Lon'], dataJson[record]['Alt'], dataJson[record]['Speed']['kmh'], dataJson[record]['Direction']))
							sPrva = False
						else:
							s.write(",\r\n\t{ \"Timestamp\":%s, \"Date\":\"%s\", \"Time\":\"%s\", \"Lat\":%s, \"Lon\":%s, \"Alt\":%s, \"Speed\":%s, \"Direction\":%s}" % (record, dataJson[record]['DateTime']['date'], dataJson[record]['DateTime']['time'], dataJson[record]['Lat'], dataJson[record]['Lon'], dataJson[record]['Alt'], dataJson[record]['Speed']['kmh'], dataJson[record]['Direction']))
				f.write("\r\n]\r\n")

		s.write("\r\n]\r\n")

	writeLog("Finished converting GPS data...")
