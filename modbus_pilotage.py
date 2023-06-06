#!/usr/bin/env python
# --------------------------------------------------------------------------- #
# Import the required libraries
# --------------------------------------------------------------------------- #
from pymodbus.server import StartAsyncTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
from RPi import GPIO
import psutil
from multiprocessing import Queue, Process
import asyncio
import logging
import lcddriver

# --------------------------------------------------------------------------- #
# Initialization
# --------------------------------------------------------------------------- #
logging.basicConfig(filename='log.log', level=logging.INFO)
log = logging.getLogger()
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(25, GPIO.OUT)

lcd = lcddriver.lcd()

# --------------------------------------------------------------------------- #
# send GPIO demand response command from modBus register value
# --------------------------------------------------------------------------- #
def setup_gpio_from_modbus_value(context):
    register = 3
    slave_id = 0x01
    address = 0x03
    value = context[slave_id].getValues(register, address)[0]
    if value > 0:
        GPIO.output(25, GPIO.HIGH)
        log.debug("Set GPIO 25 to high")
    else:
        GPIO.output(25, GPIO.LOW)
        log.debug("Set GPIO 25 to low")
    log.debug("New effacement value: " + str(value))

# --------------------------------------------------------------------------- #
# write demand response status command from GPIO state
# --------------------------------------------------------------------------- #
def write_demand_response_status_from_GPIO(context):
    register = 3
    slave_id = 0x01
    address = 0x04
    effacement = GPIO.input(25)
    values = [1]
    if effacement == 1:
        values[0] = 0
    context[slave_id].setValues(register, address, values)

# --------------------------------------------------------------------------- #
# get temperature value from sensor
# --------------------------------------------------------------------------- #
def get_temperature_value_from_sensor():
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
    temp = float(result_list[-1]) / 1000  # Temp in Celsius
    temp = temp + 1  # Correction factor
    #If you want to convert to Celsius, comment this line
    #temp = (9.0 / 5.0) * temp + 32
    if crcLine.find("NO") > -1:
        temp = -999
    log.debug(temp)
    return temp    

# --------------------------------------------------------------------------- #
# write temperature value in modBus register
# --------------------------------------------------------------------------- #
def write_temperature_value_in_modbus_register_and_lcd(context):
    register = 3
    slave_id = 0x01
    address = 0x05
    temp = get_temperature_value_from_sensor()
    
    builder = BinaryPayloadBuilder(byteorder=Endian.BIG, wordorder=Endian.BIG)
    builder.add_32bit_float(temp)
    payload = builder.to_registers()
    context[slave_id].setValues(register, address, payload)

    lcd.lcd_clear()
    lcd.lcd_display_string("    Temperature :", 1)
    lcd.lcd_display_string("      " + str(round(temp, 2)) + " .C", 3)

def setup_context():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0] * 100),
        co=ModbusSequentialDataBlock(0, [0] * 100),
        hr=ModbusSequentialDataBlock(0, [0] * 100),
        ir=ModbusSequentialDataBlock(0, [0] * 100))
    context = ModbusServerContext(slaves=store, single=True)
    return context

def setup_identity():
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'dreams by Eqinov'
    identity.ProductName = 'demo pilotage wattsense'
    identity.MajorMinorRevision = '1.0'
    return identity


async def read_context(context):
    while True:
        log.debug("Read the context")        
        setup_gpio_from_modbus_value(context)
        await asyncio.sleep(1)  # 1 second delay

async def write_context(context):
    while True:
        log.debug("Write the context")
        write_demand_response_status_from_GPIO(context)
        write_temperature_value_in_modbus_register_and_lcd(context)
        await asyncio.sleep(10)  # 30 second delay

async def run_updating_server():
    context = setup_context()
    identity = setup_identity()

    asyncio.create_task(read_context(context))
    asyncio.create_task(write_context(context))
    await StartAsyncTcpServer(context = context, identity=identity, address=("0.0.0.0", 5020))
   
if __name__ == "__main__":
    asyncio.run(run_updating_server())
