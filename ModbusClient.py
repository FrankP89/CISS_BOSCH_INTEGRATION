# -*- coding: utf-8 -*-

from pyModbusTCP.client import ModbusClient
import time
import struct

try:
    c = ModbusClient(host="10.217.185.84", port=502, auto_open=True)
    #c.debug(True)
except ValueError:
    print("Error with host or port params")

value = 43002
valuereceived = 0

ba = bytearray(struct.pack("f", value)) ## Translating information to bytes[]
ba2 = bytes(str(value), 'utf-8')        ## Translating information to bytes

while True:
    if c.is_open():
        regs_list_1 = c.read_holding_registers(420, 10)
        regs_list_2 = c.read_input_registers(100,10)
        regs_list_3 = c.read_coils(0,10)
        regs_list_4 = c.read_discrete_inputs(420,6)

        c.write_single_coil(6,True)
        c.write_multiple_registers(100,ba2)
        c.write_single_register(420,value)
        #regs_list_2_bytes = bytearray(regs_list_2)
        #regs_list_2_str = ''.join(str(e) for e in regs_list_2)

        #c.write_multiple_registers(8, ba);
        print(regs_list_1)
        print(regs_list_2)
        print(regs_list_3)
        print(regs_list_4)
        #valuereceived = struct.calcsize('f')
        #print(valuereceived)

    else:
        c.open()

    time.sleep(0.5)

