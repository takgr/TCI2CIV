import serial
import time
import codecs
import re
import websocket
import threading

# Configuration
host = "192.168.3.155"
port = 50001
sport = "/dev/ttyUSB1"
baudrate = 4800
debug = 1

# Global Variables
civ = "34"  # hardcoded
freq = ''
f = 10000000
enable_multithread = True
data = ''

def connect_serial(port, baudrate):
    while True:
        try:
            ser = serial.Serial(port, baudrate)
            print(f"Connected to serial port {port} at {baudrate} baud.")
            return ser
        except serial.SerialException as e:
            print(f"Failed to connect to serial port {port}: {e}")
            print("Retrying in 5 seconds...")
            time.sleep(5)

def on_error(ws, error):
    print(error)

def on_message(ws, message):
    global f
    if "vfo:0,0" not in message:
        if debug:
            print(message + " :Is not a frequency msg, discarding...")
    else:
        f = (message.split(",")[2]).rstrip(";")
        return f

def on_close(ws, close_status_code, close_reason):
    print("Connection closed: %s" % time.ctime())
    time.sleep(10)
    connect_websocket()  # retry after 10 seconds

def connect_websocket():
    global ws
    ws = websocket.WebSocketApp("ws://" + host + ":" + str(port),
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

def itobcd(i):
    fi = int(int(i) / 10)
    i = str(fi).zfill(9)
    out = r'\x' + i[8] + '0' + r'\x' + i[6] + i[7] + r'\x' + i[4] + i[5] + r'\x' + i[2] + i[3] + r'\x' + i[0] + i[1]
    return out

def icom_set_frequency(ser, i):
    hex = itobcd(i)
    payload = (bytes(b'\xfe\xfe\xe0\x34\x03') + codecs.escape_decode(hex)[0] + bytes(b'\xfd'))
    ser.write(payload)

def main():
    global ser
    ser = connect_serial(sport, baudrate)
    connect_websocket()

    y = ''
    while True:
        try:
            s = ser.read()
            r = (s.hex()).strip()
            y = y + r
            if y[-12:] == "fefe34e003fd":
                try:
                    ws.send("vfo:0,0;")
                except:
                    global f  # Ensure 'f' is properly referenced
                    print("Did not get frequency, retrying...")
                    f = 28000000
                    pass

                if debug:
                    print("Got echo from AMP, sending freq: " + str(f))
                time.sleep(0.1)
                icom_set_frequency(ser, f)
                y = ''
                time.sleep(0.2)
        except serial.SerialException as e:
            print(f"Serial error: {e}")
            ser.close()
            print("Reconnecting to serial port...")
            ser = connect_serial(sport, baudrate)

if __name__ == "__main__":
    main()

