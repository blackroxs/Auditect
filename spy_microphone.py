import pyaudio
import wave
from array import array
import uuid
import socket
import os
import csv
import random
import time


FORMAT=pyaudio.paInt16
CHANNELS=1
RATE=44100
CHUNK=1024
RECORD_SECONDS=5
THRESHOLD = 100
host = "192.168.58.130"                  # Change this to server IP
port = 60001                        # Reserve a port for your service.
log = "log.csv"


def connect(filename):
    s = socket.socket()             # Create a socket object
    s.connect((host, port))

    f = open(filename, "rb")
    l = f.read(1024)
    print("Sending file: " + filename)
    
    with open(log, "a") as logFile:
        writer = csv.writer(logFile)
        start = time.time()
        while (l):
            s.send(l)
            l = f.read(1024)

        end = time.time()
        elapsed = end - start

        writer.writerow([filename, start, end, elapsed])
        logFile.close()
    f.close()

    s.close()
    print("Done sending")

def send(fname):
    if(not isLogExist()):
        with open(log, "w") as logFile:
            writer = csv.writer(logFile)
            writer.writerow(["filename", "start", "end", "elapsed"])
        logFile.close()
    
    connect(fname)

def isLogExist():
    return os.path.exists(log)

def terminate(stream, audio, frames, fname):
    stream.stop_stream()
    stream.close()
    audio.terminate()
    if len(frames) > 50:
        write(audio, frames, fname)
    
def write(audio, frames, fname):
    wavfile=wave.open(fname,'wb')
    wavfile.setnchannels(CHANNELS)
    wavfile.setsampwidth(audio.get_sample_size(FORMAT))
    wavfile.setframerate(RATE)
    wavfile.writeframes(b''.join(frames))#append frames recorded to file
    wavfile.close()

    connect(fname)

def main():
    while True:
        audio = pyaudio.PyAudio() #instantiate the pyaudio
        fname = str(uuid.uuid1()) + ".wav"

        #recording prerequisites
        stream = audio.open(format=FORMAT,channels=CHANNELS, rate=RATE, input=True,frames_per_buffer=CHUNK)

        #starting recording
        frames = []

        for i in range(0,int(RATE/CHUNK*RECORD_SECONDS)):
            data = stream.read(CHUNK)
            data_chunk = array('h',data)
            vol = max(data_chunk)
            if(vol >= THRESHOLD):
                print("detected")
                frames.append(data)
            else:
                print("nothing")
                terminate(stream, audio, frames, fname)
                break
        terminate(stream, audio, frames, fname)

if __name__ == "__main__":
    main()
