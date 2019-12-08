
from pyModbusTCP.server import ModbusServer
from pyModbusTCP.client import ModbusClient
from threading import Thread, Lock
import time, struct
import serial, signal, configparser, os, csv, sys


ba = bytearray(struct.pack("f", 43200)) ## Translating information to bytes[]
ba2 = bytes(str(43200), 'utf-8')        ## Translating information to bytes

SERVER_HOST = "localhost"
SERVER_PORT = 502

# Flag for connection, initial state => down
is_modbus_server_up = False
is_modbus_client_up = False

# Define initial reconnection time (in seconds)
reconnecting_time = 1

# set global variables for communication
holding_registers = []
input_registers = []
coils = []
discrete_inputs = []

# init a thread lock
regs_lock = Lock()



def start_modbus_server(hostIP, portN):
    try:
        print("Server up and running!")
        # flag up
        is_modbus_server_up = True
        # start modbus server
        server = ModbusServer(host=hostIP, port=portN)
        # start modbus server
        server.start()

        return server

    except:
        print("Server not available ... trying to connect ...")
        # flag down
        is_modbus_server_up = False
        # start_modbus_server('10.217.185.84', 502)
        start_modbus_server(SERVER_HOST, SERVER_PORT)
        time.sleep(reconnecting_time)
        # increase a second if fails to connect
        reconnecting_time = reconnecting_time + 1

def start_modbus_client(hostIP, portN):
    try:
        print("Client connected!")
        # flag up
        is_modbus_client_up = True
        # start modbus client
        client = ModbusClient(host=hostIP, port=portN, auto_open=True)

        return client

    except:
        print("Client could not connect ... trying to connect ...")
        # flag down
        is_modbus_client_up = False
        # start_modbus_client('10.217.185.84', 502)
        start_modbus_client(SERVER_HOST, SERVER_PORT)
        time.sleep(reconnecting_time)
        # increase a second if fails to connect
        reconnecting_time = reconnecting_time + 1

def stop_modbus_server(server):
    try:
        print("Server stopped.")
        server.stop()
        # Flag for connection down
        is_modbus_server_up = False

    except:
        print("Server was not connected initially")

def stop_modbus_client(client):
    try:
        print("Client stopped.")
        client.stop()
        # Flag for connection down
        is_modbus_client_up = False

    except:
        print("Client was not connected initially")


# Use only as a polling mechanism
def polling_client_thread(hostIP, portN):
    global holding_registers
    global input_registers
    global coils
    global discrete_inputs

    client = start_modbus_client(hostIP, portN)

    while True:
        # keep TCP open
        if not client.is_open():
            client.open()

        # do modbus reading on socket
        reg_list_1 = client.read_holding_registers(420, 10)
        reg_list_2 = client.read_input_registers(100, 10)
        reg_list_3 = client.read_coils(0, 10)
        reg_list_4 = client.read_discrete_inputs(420, 6)


        client.write_single_coil(6, True)
        client.write_multiple_registers(100, ba2)
        client.write_single_register(420, 43002)

        # if read is ok, store result in regs (with thread lock synchronization)
        if reg_list_1:

            with regs_lock:
                holding_registers = list(reg_list_1)
                input_registers = list(reg_list_2)
                coils = list(reg_list_3)
                discrete_inputs = list(reg_list_4)

        # 1s before next polling
        time.sleep(1)


# Use only as a polling mechanism
def polling_client_thread_from_sensor(client, data, device, timestamp):
    global holding_registers
    global input_registers
    global coils
    global discrete_inputs

    while True:
        # keep TCP open
        if not client.is_open():
            client.open()

        ID = bytes(device, 'utf-8')  ## Translating information to bytes

        # do modbus tcp writing
        client.write_single_register(100, data[0])
        client.write_single_register(110, data[1])
        client.write_single_register(120, data[2])
        client.write_single_register(130, data[3])
        client.write_single_register(140, data[4])
        client.write_single_register(150, data[5])
        client.write_single_register(160, data[6])
        client.write_single_register(170, data[7])
        client.write_single_register(180, data[8])
        client.write_single_register(190, data[9])
        client.write_single_register(200, data[10])
        client.write_single_register(210, data[11])
        client.write_single_register(220, data[12])
        client.write_single_register(230, data[13])
        client.write_single_register(240, data[14])

        client.write_single_register(250, timestamp)
        client.write_multiple_registers(300, ID)

        # do modbus reading on socket
        reg_list_1 = client.read_holding_registers(100, 1)
        reg_list_2 = client.read_holding_registers(110, 1)
        reg_list_3 = client.read_holding_registers(120, 1)
        reg_list_4 = client.read_holding_registers(130, 1)
        reg_list_5 = client.read_holding_registers(140, 1)
        reg_list_6 = client.read_holding_registers(150, 1)
        reg_list_7 = client.read_holding_registers(160, 1)
        reg_list_8 = client.read_holding_registers(170, 1)
        reg_list_9 = client.read_holding_registers(180, 1)
        reg_list_10 = client.read_holding_registers(190, 1)
        reg_list_11 = client.read_holding_registers(200, 1)
        reg_list_12 = client.read_holding_registers(210, 1)
        reg_list_13 = client.read_holding_registers(220, 1)
        reg_list_14 = client.read_holding_registers(230, 1)
        reg_list_15 = client.read_holding_registers(240, 1)
        reg_list_16 = client.read_holding_registers(250, 1)
        reg_list_17 = client.read_holding_registers(400, 10)


        # if read is ok, store result in regs (with thread lock synchronization)
        if reg_list_1:

            with regs_lock:
                holding_registers = list(reg_list_1, reg_list_2, reg_list_3, reg_list_4, reg_list_5,
                                         reg_list_6, reg_list_7, reg_list_8, reg_list_8, reg_list_9,
                                         reg_list_10, reg_list_11, reg_list_12, reg_list_13, reg_list_14,
                                         reg_list_15, reg_list_16, reg_list_17)

        # 1s before next polling
        time.sleep(1)


def visualize_data():
    while True:
        with regs_lock:
            print("Holding registers: ", holding_registers)
            print("Input registers: ", input_registers)
            print("Coils: ", coils)
            print("Discrete inputs: ", discrete_inputs)

        time.sleep(0.5)

# start server thread
#ts = Thread(target=start_modbus_server, args=(SERVER_HOST,SERVER_PORT), name='thread_server_function').start()
# set daemon: polling thread will exit if main thread exit
# ts.daemon = True

# start client thread
# tc = Thread(target=polling_client_thread, args=(SERVER_HOST,SERVER_PORT), name='thread_client_function').start()

if __name__ == '__main__':
    time.sleep(1)
    # Function to start server
    # server = start_modbus_server(SERVER_HOST, SERVER_PORT)
    # display loop (in main thread)

    visualize_data()

