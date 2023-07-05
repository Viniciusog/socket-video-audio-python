import sys
import zmq
import time
import random
import threading
import tkinter
import cv2
import base64
import numpy as np
import socket
import pyaudio

text_port = 6000
video_port = 6001
audio_port = 6002

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Tenta se conectar a um servidor DNS
    s.connect(('8.8.8.8', 80))
    # Obtém o endereço IP local do socket
    local_ip = s.getsockname()[0]
    return local_ip

def pub_text(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    print("Conectando pub_text na porta %s\n" % port_pub)
    socket.bind("tcp://*:%s" % port_pub)
    
    topic = "*" + get_local_ip()
    while True:
        message = input()
        socket.send(b"%s %s" % (topic.encode(), message.encode()))

def sub_text(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, int(text_port)))
        socket.subscribe("*" + ip)
    
    while True:
        #200.136.196.97
        string = socket.recv()
        topic, messagedata = string.split(b" ", 1)
        print("%s: %s\n" % (topic.decode(), messagedata.decode()))

def pub_video(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)

    print("Conectando pub_video na porta %s\n" % port_pub)
    socket.bind("tcp://*:%s" % port_pub)

    camera = cv2.VideoCapture(0)

    while True:
        (grabbed, frame) = camera.read()
        frame = cv2.resize(frame, (320, 240))
        encoded, buffer = cv2.imencode('.jpg', frame)
        topic = "*" + get_local_ip()

        to_send = b'%s ' % (topic.encode())
        to_send += base64.b64encode(buffer)
        socket.send(to_send)
        
        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    camera.release()
    cv2.destroyAllWindows()

def sub_video(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)

    for ip in ips_to_connect:
        socket.connect("tcp://%s:%d" % (ip, video_port))
        topic = "*" + ip
        print("Se inscrevendo no tópico de vídeo: %s" % (topic))
        socket.subscribe(topic)

    while True:
            string = socket.recv()
            topic, frame_encoded = string.split()
            img = base64.b64decode(frame_encoded)
            npimg = np.frombuffer(img, dtype=np.uint8)
            source = cv2.imdecode(npimg, 1)
            cv2.imshow(str(topic.decode()), source)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
def pub_audio(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port_pub)

    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    stream = my_audio.open(format=format, channels=channels, rate=sample_rate, input=True, frames_per_buffer=frames_per_buffer)

    print("Enviando áudio...")
    while True: 
        data = stream.read(frames_per_buffer)
        to_send = b"%s %s" % (b"*", data)
        socket.send(to_send)

def sub_audio(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    """ for ip in ips_to_connect: """
    for ip in ips_to_connect:
        print("Conectando em %s" % ip)
        socket.connect("tcp://%s:%s" % (ip, audio_port))
    
    socket.subscribe("*") 

    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    stream = my_audio.open(format=format, channels=channels, rate=sample_rate, output=True, frames_per_buffer=frames_per_buffer)

    print("Recebendo áudio...")
    cont = 0
    while True:
        string = socket.recv()
        if cont == 0:
            print(string)

        topic, data = string.split(b' ', 1)

        if cont == 0:
            print("topic")
            print(topic)
            print("data")
            print(data)
            cont += 1

        stream.write(data)

strArgv = ""
for element in sys.argv[1:]:
    strArgv += str(element) + " "
strArgv = strArgv.strip()

print(":%s:" % (strArgv))

nodes = strArgv.split("-node ")
print("nodes")
print(nodes)
for i in range(1, len(nodes)-1):
    nodes[i] = nodes[i].strip()

# Se tiver -sub, os pubs não vão executar
type_of_execution = nodes[0] 
print("Tipo de execução:%s:" % (type_of_execution))
nodes = nodes[1:]
print(nodes)

# Criando contexto
context = zmq.Context()

thread_pub = threading.Thread(target=pub_text, args=(text_port, context))
thread_pub.start()

thread_sub = threading.Thread(target=sub_text, args=(nodes, context))
thread_sub.start()

thread_pub_video = threading.Thread(target=pub_video, args=(video_port, context))
thread_pub_video.start()

thread_sub_video = threading.Thread(target=sub_video, args=(nodes, context))
thread_sub_video.start()

thread_pub_audio = threading.Thread(target=pub_audio, args=(audio_port, context))
thread_pub_audio.start()
time.sleep(1)
thread_sub_audio = threading.Thread(target=sub_audio, args=(nodes, context))
thread_sub_audio.start()

thread_pub.join()
thread_sub.join()
thread_pub_video.join()
thread_sub_video.join()
thread_pub_audio.join()
thread_sub_audio.join()

