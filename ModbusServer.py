
from pyModbusTCP.server import ModbusServer
import time
import struct


def start_server(hostIP, portN):
    try:
        # start modbus server
        server = ModbusServer(host=hostIP, port=portN)
        # start modbus server
        server.start()

        # flag up
        is_server_up = True
        print("Server up and running!")

    except:
        print("Server not available ... trying to connect ...")
        start_server('10.217.185.84', 502)
        time.sleep(reconnecting_time)
        # increase a second if fails to
        reconnecting_time = reconnecting_time + 1

def stop_server(server):
    try:
        print("Server stopped.")
        server.stop()

    except:
        print("Server not connected in the first place.")


if __name__ == '__main__':
    # Define initial reconnection time
    reconnecting_time = 1
    # Flag for connection up
    is_server_up = False

    # Function to start server
    start_server('10.217.185.84', 502)
