#! /usr/bin/env python3

from collections import Counter
from threading import Thread
import scapy.all as scapy
import time
import matplotlib.pyplot as plt
import numpy as np
import simpleaudio as sa


## Create a Packet Counter
packet_counts = Counter()
data_size = []
data_time = []
audio_signal = []
audio_time = []
start_time = time.time()
swtich = 0

def set_packet(size, time):
    time = int(time - start_time)
    if len(data_size) > time:
        data_size[time] = data_size[time] + size
    else:
        data_size.append(size)
        data_time.append(time)
    
## Define our Custom Action function
def custom_action(packet):
    # Create tuple of Src/Dst in sorted order
    if scapy.Raw in packet:
        key = tuple(sorted([packet[0][1].src, packet[0][1].dst]))
        set_packet(1, packet.time)
        packet_counts.update([key])
        #return f"Packet #{sum(packet_counts.values())} [{packet.time}]: {packet[0][1].src} ==> {packet[0][1].dst}"
    else:
        set_packet(0, packet.time)

def generate_signal():
    frequency = 440  # Our played note will be 440 Hz
    fs = 44100  # 44100 samples per second
    seconds = 3  # Note duration of 3 seconds
    
    # Generate array with seconds*sample_rate steps, ranging between 0 and seconds
    t = np.linspace(0, seconds, seconds * fs, False)

    # Generate a 440 Hz sine wave
    note = np.sin(frequency * t * 2 * np.pi)
    silence = np.sin(0 * t * 2 * np.pi)
    
    # Ensure that highest value is in 16-bit range
    beep = note * (2**15 - 1) / np.max(np.abs(note))
    
    audio = silence
    
    t = 0
    for j in range(seconds + 1):
        audio_signal.append(0)
        audio_time.append(t + j)
    t += seconds
    
    for i in range(5):
        audio = np.append(audio, beep)
        for j in range(i * seconds, (i + 1) * seconds + 1):
            audio_signal.append(1)
            audio_time.append(t + j)
        t += seconds
        audio = np.append(audio, silence)
        for j in range(i * seconds, (i + 1) * seconds + 1):
            audio_signal.append(0)
            audio_time.append(t + j)

            
    # Convert to 16-bit data
    audio = audio.astype(np.int16)

    # Start playback
    play_obj = sa.play_buffer(audio, 1, 2, fs)

    # Wait for playback to finish before exiting
    play_obj.wait_done()

def process_sniff():
    print("Start: " + str(start_time))
    scapy.sniff(prn=custom_action, timeout=45)

def main():
    t1 = Thread(target=generate_signal)
    t2 = Thread(target=process_sniff)
    print("Sending sound signal...")
    t1.start()
    print("Starting network sniffer...")
    t2.start()
    # Have to find a way to end sniff after signal ends
    t1.join()
    print("Sound signal sent")
    t2.join()

    
    
    plt.subplot(2, 1, 1)
    plt.xlabel('Time (s)')
    plt.ylabel('Packet/1 sec')
    plt.title('Packet count')
    plt.plot(np.array(data_time), np.array(data_size))
    plt.subplot(2, 1, 2)
    plt.xlabel('Time (s)')
    plt.ylabel('Audio Playing')
    plt.title('Audio Signals')
    plt.plot(np.array(audio_time), np.array(audio_signal))
    plt.show()
if __name__ == '__main__':
    main()
