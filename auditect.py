#! /usr/bin/env python3

from collections import Counter
from threading import Thread
import scapy.all as scapy
import time
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import simpleaudio as sa


## Create a Packet Counter
packet_counts = Counter()
data_size = []
data_time = []
audio_signal = []
audio_time = []
start_time = 0
swtich = 0
packet_threshold = 0
time_threshold = 3
trial = 2

def set_packet(size, time):
    time = int(time - start_time)
    index = data_time.index(time)
    data_size[index] = data_size[index] + 1 
    
    
## Custom analysis of packet
def analyse(packet):
    # Create tuple of Src/Dst in sorted order
    if scapy.Raw in packet:
        key = tuple(sorted([packet[0][1].src, packet[0][1].dst]))
        set_packet(1, packet.time)
        packet_counts.update([key])
        #return f"Packet #{sum(packet_counts.values())} [{packet.time}]: {packet[0][1].src} ==> {packet[0][1].dst}"
    else:
        set_packet(0, packet.time)

def get_threshold(packet):
    if scapy.Raw in packet:        
        key = tuple(sorted([packet[0][1].src, packet[0][1].dst]))
        packet_counts.update([key])
        #return f"Packet #{sum(packet_counts.values())}: {packet[0][1].src} ==> {packet[0][1].dst}"

def generate_signal():
    global trial
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
    
    for i in range(trial):
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
    
def reduce_traffic():
    global packet_threshold
    
    reduced_data = []
    for i in data_size:
        if i > packet_threshold:
            reduced_data.append(1)
        else:
            reduced_data.append(0)
            
    return reduced_data
    
def structure_reduced_graph(reduced_data):
    global data_time
    
    new_reduced = []
    new_time = []
    for i in range(len(reduced_data)):
        if reduced_data[i] == 1:
            if i - 1 >= 0:
                prev = reduced_data[i-1]
                if prev == 0:
                    new_time.append(data_time[i])
                    new_reduced.append(0)
                    new_reduced.append(1)
                    new_time.append(data_time[i])
            if i + 1 < len(reduced_data):
                forward = reduced_data[i+1]
                if forward == 0:
                    new_time.append(data_time[i])
                    new_reduced.append(1)
                    new_reduced.append(0)
                    new_time.append(data_time[i])
        else:
            new_time.append(data_time[i])
            new_reduced.append(reduced_data[i])
    
    data_time = new_time
    
    print(new_reduced)
    print(new_time)
    
    return new_reduced
    
def is_spy_microphone(reduced_data, audio_signal):
    global time_threshold
    global trial
    
    confidence = 0.0
    
    for i in range(0, len(audio_signal)):
        if i + 1 < len(audio_signal):
            if audio_signal[i] == 1 and audio_signal[i+1] == 0:
                limit = i + time_threshold
                if limit > len(reduced_data):
                    limit = len(reduced_data)
                for k in range(i, limit):
                    if reduced_data[k] == 1:
                        confidence = confidence + 1
                        break
    
    return (confidence/trial)*100
    

def init_sniff(sniff_time):
    for i in range(0, sniff_time + 1):
        data_time.append(i)
        data_size.append(0)
        
    global start_time
    start_time = time.time()
    

def set_baseline():
    baseline_time = 5
    scapy.sniff(prn=get_threshold, timeout=baseline_time)
    
    global packet_threshold
    packet_threshold = sum(packet_counts.values())/baseline_time
    
    print(f"Count = {sum(packet_counts.values())}")
    print(f"Average = {packet_threshold}")

def process_sniff():
    sniff_time = 21
    init_sniff(sniff_time)
    print("Start: " + str(start_time))
    scapy.sniff(prn=analyse, timeout=sniff_time)
    

def main():
    set_baseline()

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
    
    gs = gridspec.GridSpec(3, 2)

    plt.subplot(gs[0, :])
    plt.xlabel('Time (s)')
    plt.ylabel('Packet/1 sec')
    plt.title('Packet count')
    plt.xticks(range(0, max(data_time) + 1))
    plt.plot(np.array(data_time), np.array(data_size))
    
    reduced_data = structure_reduced_graph(reduce_traffic())
    confidence = is_spy_microphone(reduced_data, audio_signal)
    
    print("Confidence that there is a spy microphone: " + str(confidence))
    
    plt.subplot(gs[1, :])
    plt.xlabel('Time (s)')
    plt.ylabel('Data Sent')
    plt.title('Packet count')
    plt.xticks(range(0, max(data_time) + 1))
    plt.plot(np.array(data_time), np.array(reduced_data))
    
    plt.subplot(gs[2, :])
    plt.xlabel('Time (s)')
    plt.ylabel('Audio Playing')
    plt.title('Audio Signals')
    plt.plot(np.array(audio_time), np.array(audio_signal))
    plt.xticks(range(0, max(data_time) + 1))
    plt.show()
    
    
if __name__ == '__main__':
    main()
