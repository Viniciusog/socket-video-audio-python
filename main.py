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
    topics_to_subscribe = []

    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, int(video_port)))
        topic = "*" + ip
        topics_to_subscribe.append(topic)
    
    socket.subscribe("*")

    for topic_to_subscribe in topics_to_subscribe:
        print("Subscribing to %s\n" % (topic_to_subscribe))
        socket.subscribe(topic_to_subscribe)

    while True:
        try:
            string = socket.recv()
            topic, frame_encoded = string.split()
            img = base64.b64decode(frame_encoded)
            npimg = np.frombuffer(img, dtype=np.uint8)
            source = cv2.imdecode(npimg, 1)
            cv2.imshow(str(topic.decode()), source)
            cv2.waitKey(1)
        except KeyboardInterrupt:
            cv2.destroyWindow()
            break

strArgv = ""
for element in sys.argv[1:]:
    strArgv += str(element) + " "
strArgv = strArgv.strip()

print(":%s:" % (strArgv))

nodes = strArgv.split("-node ")
for i in range(1, len(nodes)-1):
    nodes[i] = nodes[i].strip()

# Se tiver -sub, os pubs não vão executar
type_of_execution = nodes[0] 
print("Tipo de execução: %s:" % (type_of_execution))
nodes = nodes[1:]
print(nodes)

# Criando contexto
context = zmq.Context()

if type_of_execution != "-sub ":
    thread_pub = threading.Thread(target=pub_text, args=(text_port, context))
    thread_pub.start()

thread_sub = threading.Thread(target=sub_text, args=(nodes, context))
thread_sub.start()

if type_of_execution != "-sub ":
    thread__pub_video = threading.Thread(target=pub_video, args=(video_port, context))
    thread__pub_video.start()

thread__sub_video = threading.Thread(target=sub_video, args=(video_port, nodes, context))
thread__sub_video.start()