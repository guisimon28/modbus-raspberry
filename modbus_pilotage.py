#!/usr/bin/env python
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.server.async import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from RPi import GPIO
import psutil
from multiprocessing import Queue, Process
from twisted.internet.task import LoopingCall
import logging
import lcddriver


# --------------------------------------------------------------------------- #
# Initalisation
# --------------------------------------------------------------------------- #
logging.basicConfig(filename='log.log',level=logging.INFO)
log = logging.getLogger()
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)

lcd = lcddriver.lcd()


# --------------------------------------------------------------------------- #
# read in register to set GPIO state
# --------------------------------------------------------------------------- #
def read_context(a):    
    log.debug("read the context")
    context = a[0]
    register = 3
    slave_id = 0x01
    address = 0x01
    value = context[slave_id].getValues(register, address)[0]
    if value > 0 :		
	GPIO.output(25, GPIO.HIGH)
	log.debug("set gpio 25 high")	
    else:	
	GPIO.output(25, GPIO.LOW)
	log.debug("set gpio 25 low")
    log.debug("new value: " + str(value))

# --------------------------------------------------------------------------- #
# write in register to set temperature from DS18B20
# --------------------------------------------------------------------------- #
def write_context(a):    
	log.debug("write the context")
	context = a[0]
	register = 4
	slave_id = 0x01
	address = 0x00
	sensorpath = '/sys/bus/w1/devices/28-00000adfed51'
	try:
		f = open(sensorpath + "/w1_slave", 'r')
	except IOError as e:
		return -999
	lines = f.readlines()
	f.close()
	crcLine = lines[0]
	tempLine = lines[1]
	result_list = tempLine.split("=")
	temp = float(result_list[-1]) / 1000  # temp in Celcius
	temp = temp + 1  # correction factor
	# if you want to convert to Celcius, comment this line
	#temp = (9.0 / 5.0) * temp + 32
	if crcLine.find("NO") > -1:
		temp = -999
	log.debug(temp)
	builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
	builder.add_32bit_float(temp)
	payload = builder.to_registers()
	context[slave_id].setValues(register, address, payload)

	address = 0x03
	effacement = GPIO.input(25)
	values = [1]
	if (effacement == 1):
    		values[0] = 0
	context[slave_id].setValues(register, address, values)
	lcd.lcd_clear()
	lcd.lcd_display_string("    Temperature :", 1)
	lcd.lcd_display_string("      "+str(round(temp, 2))+" .C", 3)


def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, [0]*100),
        hr=ModbusSequentialDataBlock(0, [0]*100),
        ir=ModbusSequentialDataBlock(0, [0]*100))
    context = ModbusServerContext(slaves=store, single=True)
    
    # ----------------------------------------------------------------------- # 
    # initialize the server information
    # ----------------------------------------------------------------------- # 
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'dreams by Eqinov'
    identity.ProductName = 'demo pilotage wattsense'
    identity.MajorMinorRevision = '1.0'
    
    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    timeRead = 1  # 1 second delay
    readLoop = LoopingCall(f=read_context, a=(context,))
    readLoop.start(timeRead, now=False) # initially delay by time	
	
    timeWrite = 30  # 1 second delay
    writeLoop = LoopingCall(f=write_context, a=(context,))
    writeLoop.start(timeWrite, now=False) # initially delay by time	
    StartTcpServer(context, identity=identity, address=("0.0.0.0", 5020))


if __name__ == "__main__":
    run_updating_server()