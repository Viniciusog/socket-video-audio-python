# digite pip install -r requirements.txt para instalar as dependências
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

STOP_VIDEO = "#stopvideo"
STOP_AUDIO = "#stopaudio"
EXIT = 0

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Tenta se conectar a um servidor DNS
    s.connect(('8.8.8.8', 80))
    # Obtém o endereço IP local do socket
    local_ip = s.getsockname()[0]
    return local_ip

def quit_socket(socket):
    topic = "quit-" + get_local_ip()
    to_send = b"%s %s" % (topic.encode(), b"Nothing")
    socket.send(to_send)

def pub_text(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)    
    socket.bind("tcp://*:%s" % port_pub)
    
    topic = "*" + get_local_ip()
    print("|---------------Chat---------------|")
    while True:
        message = input()
        if message == "#quit":
            quit_socket(socket)
            global EXIT
            EXIT = 1
            break
        socket.send(b"%s %s" % (topic.encode(), message.encode()))
    
    print("Saindo pub_text")
    socket.close()

def sub_text(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, int(text_port)))
        socket.subscribe("*" + ip)
        socket.subscribe("quit-" + ip)
    
    while True: 
        #200.136.196.97
        string = socket.recv()
        topic, messagedata = string.split(b" ", 1)

        # Se recebermos uma mensagem de saída, então mostramos que o usuário está saindo.
        if topic.decode().startswith("quit"):            
            ip_user_quitting = topic.decode().split("-")[1]
            print("Usuário %s saiu do canal de texto." % (ip_user_quitting))
            # Se o EXIT = 1, então significa que nós mesmos estamos saindo 
            if EXIT:
                break
            continue

        print("%s: %s\n" % (topic.decode(), messagedata.decode()))
    
    print("Saindo sub_text")
    socket.close()

def pub_video(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)

    socket.bind("tcp://*:%s" % port_pub)

    camera = cv2.VideoCapture(0)

    quitting_key_q = 0

    while not EXIT:
        (grabbed, frame) = camera.read()
        frame = cv2.resize(frame, (320, 240))
        encoded, buffer = cv2.imencode('.jpg', frame)
        topic = "*" + get_local_ip()

        to_send = b'%s ' % (topic.encode())
        buffer_encoded = base64.b64encode(buffer)
        to_send += buffer_encoded
        socket.send(to_send)
        
        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            quitting_key_q = 1
            # ? Colocar exit = 1 aqui ??
            quit_socket(socket)
            break

    camera.release()

    if not quitting_key_q:
        quit_socket(socket)

    cv2.destroyWindow('Webcam')
    socket.close()
    print("Saindo pub_video")

def sub_video(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)

    for ip in ips_to_connect:
        socket.connect("tcp://%s:%d" % (ip, video_port))
        topic = "*" + ip
        socket.subscribe(topic)
        quit_topic = "quit-" + ip
        socket.subscribe(quit_topic)

    # Se digitarmos q na webcam, iremos executar o quitting, mas o exit aidna será 0.
    # o exit ainda será 0. Em seguida, quando 
    while True:
        string = socket.recv()
        topic, frame_encoded = string.split()

        # Significa que um determinado usuário está saindo
        if topic.decode().startswith("quit"):   
            print("topic começa com quit - sub video")
            ip_user_quitting = topic.decode().split("-")[1]
            print("Usuário %s saiu do canal de vídeo. Removendo janela.." % (ip_user_quitting))
            cv2.destroyWindow(ip_user_quitting)
            # Se EXIT = 1, então somos nós mesmos que estamos saindo 
            if EXIT:
                break
            continue

        img = base64.b64decode(frame_encoded)
        npimg = np.frombuffer(img, dtype=np.uint8)
        source = cv2.imdecode(npimg, 1)
        cv2.imshow(str(topic.decode()[1:]), source)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Tecla q Pressionada. Removendo janela da minha Webcam..")
            break

    socket.close()
    print("Saindo sub_video")
        
def pub_audio(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port_pub)

    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    stream = my_audio.open(format=format, channels=channels, rate=sample_rate, input=True, frames_per_buffer=frames_per_buffer)

    while not EXIT: 
        data = stream.read(frames_per_buffer)
        to_send = b"%s %s" % (b"*", data)
        socket.send(to_send)

    quit_socket(socket)
    socket.close()
    print("Saindo pub_audio")

def sub_audio(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, audio_port))
        socket.subscribe("quit-" + ip)
    
    socket.subscribe("*") 

    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    stream = my_audio.open(format=format, channels=channels, rate=sample_rate, output=True, frames_per_buffer=frames_per_buffer)

    cont = 0
    while True:
        string = socket.recv()

        topic, data = string.split(b' ', 1)

        # Significa que algum usuário está saindo
        if topic.decode().startswith("quit"): 
            ip_user_quitting = topic.decode().split("-")[1]
            print("Usuário %s saiu do canal de áudio." % (ip_user_quitting))
            # Se EXIT = 1, então somos nós mesmos que estamos saindo 
            if EXIT:
                break
            continue

        stream.write(data)
    socket.close()
    print("Saindo sub_audio")

# Pegando os parâmetros quando executar o arquivo
strArgv = ""
for element in sys.argv[1:]:
    strArgv += str(element) + " "
strArgv = strArgv.strip()

#print(":%s:" % (strArgv))

nodes = strArgv.split("-node ")
print("Nós para conectar:")
for i in range(1, len(nodes)-1):
    nodes[i] = nodes[i].strip()

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
