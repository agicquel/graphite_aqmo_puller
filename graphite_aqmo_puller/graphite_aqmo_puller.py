import re
import os
import sys
import http.client
import mimetypes
import json
import pickle
import time
import datetime
import socket
import struct
import threading

AUTH = str(os.environ['AUTH'])
CARBON_SERVER = str(os.environ['CARBON_SERVER'])
CARBON_PICKLE_PORT = int(os.environ['CARBON_PICKLE_PORT'])

def getOPCSensors():
    conn = http.client.HTTPSConnection("data.aqmo.org")
    headers = {
    'Authorization': 'Basic ' + AUTH
    }
    conn.request("GET", "/api/sensors", '', headers)
    res = conn.getresponse()
    data = res.read()
    return list(filter(lambda s: 'OPC_N3' in s, json.loads(data.decode("utf-8"))))

def getMetricsSensor(sensor):
    conn = http.client.HTTPSConnection("data.aqmo.org")
    headers = {
    'Authorization': 'Basic ' + AUTH
    }
    conn.request("GET", "/api/measures?sensor=" + sensor, '', headers)
    res = conn.getresponse()
    data = res.read()

    try:
        decoded_data = json.loads(data.decode("utf-8"))
    except Exception:
        return ()
    
    values = decoded_data[0]['properties'][sensor][1]
    position = decoded_data[0]['geometry']['coordinates']
    timestamp = datetime.datetime.strptime(values['t'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

    metrics = []
    metrics.append(("sensor." + sensor + ".value", (timestamp, values['v'])))
    metrics.append(("sensor." + sensor + ".lon", (timestamp, position[0])))
    metrics.append(("sensor." + sensor + ".lat", (timestamp, position[1])))
    return metrics

def sendPickle(metrics):
    payload = pickle.dumps(metrics, protocol=2)
    header = struct.pack('!L', len(payload))
    message = header + payload
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((CARBON_SERVER, CARBON_PICKLE_PORT))
    except socket.error as msg:
        print(msg)
        print('Could not open socket: ' + CARBON_SERVER + ':' + str(CARBON_PICKLE_PORT))
        sys.exit(1)
    sock.send(message)
    sock.close()
    

def run(sensor, delay):
    while True:
        metrics = getMetricsSensor(sensor)
        print("Sending " + sensor + " data to carbon server...", end = '')
        sendPickle(metrics)
        print(" Done.")
        time.sleep(delay)

def main():
    print("Retrieving sensors list...")
    try:
        for sensor in getOPCSensors():
            print("Launch thread for sensors : " + sensor)
            thread = threading.Thread(target=run, args=[sensor, 20])
            thread.start()
            time.sleep(2)
    except KeyboardInterrupt:
        sys.stderr.write("\nExiting on CTRL-c\n")
        sys.exit(0)

if __name__ == "__main__":
    main()

