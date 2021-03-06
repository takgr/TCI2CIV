import serial
import time
import codecs
import re
import websocket
import threading

host = "localhost"
port = 40001
sport = "COM4"
ser = serial.Serial(sport, 4800)
#i = 707400
civ = "34" #hardcoded
debug = 1
freq = ''
f = 10000000

data = ''
                           
def on_error(ws, error):
    print(error)

def on_message(ws, message):
    global f
    if "vfo:0,0" not in message:
        if debug: print(message + " :Is not a frequency msg, discarding...")
    else:
        #print(message)
        f = (message.split(",")[2]).rstrip(";")
        #print(f)
        return f

def on_close(ws, close_status_code, close_reason):
    print("### closed ###")

if __name__ == "__main__":
    #websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://" + host + ":" + str(port),
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

    conn_timeout = 5
    while not ws.sock.connected and conn_timeout:
        time.sleep(1)
        conn_timeout -= 1

#    ws.on_open = on_open


def itobcd(i):
    fi = int(int(i)/10)
    i = str(fi).zfill(9)
    out =  r'\x'+i[8]+'0'+r'\x'+i[6]+i[7]+r'\x'+i[4]+i[5]+r'\x'+i[2]+i[3]+r'\x'+i[0]+i[1]
#   print(out)
    return out


def icom_set_frequency(i):
    hex = itobcd(i)
    payload = (bytes(b'\xfe\xfe\xe0\x34\x03')+codecs.escape_decode(hex)[0]+bytes(b'\xfd'))
    send = ser.write(payload)
#    print(payload.hex())

y = ''
while 1:
    s = ser.read()
    r = (s.hex()).strip()
    y = y + r
    if y[-12:] == "fefe34e003fd":
        ws.send("vfo:0,0;")
        time.sleep(0.2)
        if debug : print("Got echo from AMP, sending freq : " + str(f))
        time.sleep(0.1)
        icom_set_frequency(f)
        y = ''
        time.sleep(0.2)
