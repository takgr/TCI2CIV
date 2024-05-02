import serial
import time
import codecs
import re
import websocket
import threading

host = "192.168.3.155"
port = 50001
sport = "/dev/ttyUSB0"
ser = serial.Serial(sport, 4800)
#i = 707400
civ = "34" #hardcoded
debug = 1
freq = ''
f = 10000000
enable_multithread=True
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
    print ("Connection closed: %s" % time.ctime())
    time.sleep(10)
    connect_websocket() # retry per 10 seconds

def connect_websocket():
    #websocket.enableTrace(True)
    global ws
    ws = websocket.WebSocketApp("ws://" + host + ":" + str(port),
                                on_message = on_message,
                                on_error = on_error,
                                on_close = on_close)
    wst = threading.Thread(target=ws.run_forever)
    wst.daemon = True
    wst.start()

if __name__ == "__main__":
    try:
        connect_websocket()
        time.sleep(10)
    except Exception as err:
        print(err)
        print("connect failed")

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
        try:
            ws.send("vfo:0,0;")
        except:    
            print("Did not get frequency, retrying...")
            #connect_websocket()
            f = 28000000
            pass
#        time.sleep(0.2)
        if debug : print("Got echo from AMP, sending freq : " + str(f))
        time.sleep(0.1)
        icom_set_frequency(f)
        y = ''
        time.sleep(0.2)
