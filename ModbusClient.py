# -*- coding: utf-8 -*-

from pyModbusTCP.client import ModbusClient
import time
import struct

try:
    c = ModbusClient(host="localhost", port=502, auto_open=True)
    #c.debug(True)
except ValueError:
    print("Error with host or port params")

value = 43002
valuereceived = 0

ba = bytearray(struct.pack("f", value)) ## Translating information to bytes[]
ba2 = bytes(str(value), 'utf-8')        ## Translating information to bytes

buff = [1,2,3,4,5,6,7,8,9,10,12,13,14,15,16]

while True:
    if c.is_open():
        regs_list_1 = c.read_holding_registers(100, 15)
        regs_list_2 = c.read_input_registers(110,10)
        regs_list_3 = c.read_coils(0,10)
        regs_list_4 = c.read_discrete_inputs(200,6)

        # Accelerometer
        #c.write_single_register(100, buff[0])
        #c.write_single_register(101, buff[1])
        #c.write_single_register(102, buff[2])
        ## Gyroscope
        #c.write_single_register(103, buff[3])
        #c.write_single_register(104, buff[4])
        #c.write_single_register(105, buff[5])
        # Magnetometer
        #c.write_single_register(106, buff[6])
        #c.write_single_register(107, buff[7])
        #c.write_single_register(108, buff[8])
        # Temperature
        #c.write_single_register(109, buff[9])
        # Pressure
        #c.write_single_register(110, buff[10])
        # Humidity
        #c.write_single_register(111, buff[11])
        # Light
        #c.write_single_register(112, buff[12])
        # Acoustic - Noise
        #c.write_single_register(113, buff[13])
    
        #c.write_single_register(240, buff[14])
        
        #c.write_single_coil(6,True)
        #c.write_multiple_registers(100,ba2)
        #c.write_single_register(420,value)
        #regs_list_2_bytes = bytearray(regs_list_2)
        #regs_list_2_str = ''.join(str(e) for e in regs_list_2)

        #c.write_multiple_registers(8, ba);
        print(regs_list_1)
        #print(regs_list_2)
        #print(regs_list_3)
        #print(regs_list_4)
        #valuereceived = struct.calcsize('f')
        #print(valuereceived)

    else:
        c.open()

    time.sleep(0.5)

