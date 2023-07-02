# Subscribers are created with ZMQ.SUB socket types.
# A zmq subscriber can connect to many publishers.
import sys
import zmq
import time
import random
import threading
import tkinter
import cv2
import base64
import numpy as np

text_port = 6000
video_port = 6001
audio_port = 6002

# criar função para pub e função para sub
# cada uma dessas funções será executada em uma thread diferente (para ser multithread)
def pub_function(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    print("Conectando pub_text na porta %s\n" % port_pub)
    socket.bind("tcp://*:%s" % port_pub)

    while True:
        topic = random.randrange(9999,10005)
        topic = "*"
        messagedata = random.randrange(1,215) - 80
        print("%s %d" % (topic, messagedata))
        socket.send(b"%s %d" % (topic.encode(), messagedata))
        time.sleep(1)

def sub_function(port_pub, array_ports_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    for port_to_connect in array_ports_connect:
        socket.connect("tcp://localhost:%s" % int(port_to_connect))
    # Aqui estamos nos inscrevendo em todos os conteúdos que tiverem a nossa porta
    # pois assim, saberemos que a mensagem é para a gente
    socket.subscribe(port_pub)
    # Aqui estamos nos inscrevendo no conteúdo que começar com *
    socket.subscribe("*")

    while True:
        string = socket.recv()
        topic, messagedata = string.split()
        print("Mensagem recebida: %s, tópico: %s\n" % (messagedata, topic))

def pub_video(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)

    print("Conectando pub_video na porta %s\n" % port_pub)
    socket.bind("tcp://*:%s" % port_pub)

    camera = cv2.VideoCapture(0)

    while True:
        (grabbed, frame) = camera.read()
        encoded, buffer = cv2.imencode('.jpg', frame)
        topic = "*" + port_pub

        to_send = b'%s ' % (topic.encode())
        to_send += base64.b64encode(buffer)
        socket.send(to_send)
        
        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    camera.release()
    cv2.destroyAllWindows()

def sub_video(port_pub, array_ports_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    topics_to_subscribe = []

    for port_to_connect in array_ports_connect:
        socket.connect("tcp://localhost:%s" % int(port_to_connect))
        topic = "*" + port_to_connect
        topics_to_subscribe.append(topic)
    
    socket.subscribe(port_pub)

    for topic_to_subscribe in topics_to_subscribe:
        print("\nSubscribing to %s\n" % (topic_to_subscribe))
        socket.subscribe(topic_to_subscribe)

    while True:
        try:
            string = socket.recv()
            topic, frame_encoded = string.split()
            img = base64.b64decode(frame_encoded)
            npimg = np.frombuffer(img, dtype=np.uint8)
            source = cv2.imdecode(npimg, 1)
            cv2.imshow(str(topic), source)
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
nodes = nodes[1:]
print(nodes)

# Socket to talk to server
context = zmq.Context()

thread_pub = threading.Thread(target=pub_function, args=(text_port, context))
thread_pub.start()

thread_sub = threading.Thread(target=sub_function, args=(text_port, text_ports_to_connect, context))
thread_sub.start()

thread__pub_video = threading.Thread(target=pub_video, args=(portas_pubs[1], context))
thread__pub_video.start()

thread__pub_video = threading.Thread(target=sub_video, args=(portas_pubs[1], video_ports_to_connect, context))
thread__pub_video.start()

""" print("Subscribing to ports....")
for i in ports_subscribe:
    print("Subscribing to " + i)
    socketSub.connect("tcp://localhost:%s" % int(i)) """

# Subscribes to all topics you can selectively create multiple workers
# that would be responsible for reading from one or more predefined topics
# if you have used AWS SNS this is a simliar concept

""" socketSub.subscribe("*") # se o tópico da mensagem for público para todos que estiverem ouvindo
socketSub.subscribe("")
socketSub.subscribe(port_pub) # se o tópico da mensagem for pra mim (minha porta)

while True:
    # Receives a string format message
    print(socketSub.recv()) """