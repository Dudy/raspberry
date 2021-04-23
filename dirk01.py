'''
**********************************************************************
* Filename    : dirk1.py
* Description : test for SunFoudner DHT11 humiture & temperature module
* Author      : Dirk Podolak
* E-mail      : dirk.podolak@gmail.com
* Website     : www.podolak.de
* Update      : 2021-04-22
**********************************************************************
'''
#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime, timezone

LedPin = 17
dhtPin = 27

GPIO.setmode(GPIO.BCM)
GPIO.setup(LedPin, GPIO.OUT, initial=GPIO.HIGH)

MAX_UNCHANGE_COUNT = 100

STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5

def readDht11():
	GPIO.setup(dhtPin, GPIO.OUT)
	GPIO.output(dhtPin, GPIO.HIGH)
	time.sleep(0.05)
	GPIO.output(dhtPin, GPIO.LOW)
	time.sleep(0.02)
	GPIO.setup(dhtPin, GPIO.IN, GPIO.PUD_UP)

	unchanged_count = 0
	last = -1
	data = []
	while True:
		current = GPIO.input(dhtPin)
		data.append(current)
		if last != current:
			unchanged_count = 0
			last = current
		else:
			unchanged_count += 1
			if unchanged_count > MAX_UNCHANGE_COUNT:
				break

	state = STATE_INIT_PULL_DOWN

	lengths = []
	current_length = 0

	for current in data:
		current_length += 1

		if state == STATE_INIT_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_INIT_PULL_UP
			else:
				continue
		if state == STATE_INIT_PULL_UP:
			if current == GPIO.HIGH:
				state = STATE_DATA_FIRST_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_FIRST_PULL_DOWN:
			if current == GPIO.LOW:
				state = STATE_DATA_PULL_UP
			else:
				continue
		if state == STATE_DATA_PULL_UP:
			if current == GPIO.HIGH:
				current_length = 0
				state = STATE_DATA_PULL_DOWN
			else:
				continue
		if state == STATE_DATA_PULL_DOWN:
			if current == GPIO.LOW:
				lengths.append(current_length)
				state = STATE_DATA_PULL_UP
			else:
				continue
	if len(lengths) != 40:
		#print ("Data not good, skip")
		return False

	shortest_pull_up = min(lengths)
	longest_pull_up = max(lengths)
	halfway = (longest_pull_up + shortest_pull_up) / 2
	bits = []
	the_bytes = []
	byte = 0

	for length in lengths:
		bit = 0
		if length > halfway:
			bit = 1
		bits.append(bit)
	#print ("bits: %s, length: %d" % (bits, len(bits)))
	for i in range(0, len(bits)):
		byte = byte << 1
		if (bits[i]):
			byte = byte | 1
		else:
			byte = byte | 0
		if ((i + 1) % 8 == 0):
			the_bytes.append(byte)
			byte = 0
	#print (the_bytes)
	checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
	if the_bytes[4] != checksum:
		#print ("Data not good, skip")
		return False

	return the_bytes[0], the_bytes[1], the_bytes[2], the_bytes[3]

def main():
	while True:
		result = readDht11()
		if result:
			humidity_high, humidity_low, temperature_high, temperature_low = result

			if humidity_high >= 50:
				# Turn on LED
				GPIO.output(LedPin, GPIO.LOW)
			else:
				# Turn off LED
				GPIO.output(LedPin, GPIO.HIGH)

			now = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
			print ("timestamp: %s, humidity: %s.%s %%,  Temperature: %s.%s C`" % (now, humidity_high, humidity_low, temperature_high, temperature_low))
			with open('temperatureAndHumidity.csv', 'a', newline='') as csvfile:
				csvwriter = csv.writer(csvfile)
				csvwriter.writerow([now, humidity_high, humidity_low, temperature_high, temperature_low])
		time.sleep(1)

def destroy():
	GPIO.output(LedPin, GPIO.HIGH)
	GPIO.cleanup()

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		destroy() 

