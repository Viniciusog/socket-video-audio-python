import zmq
import pyaudio
import time

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

def sub_audio(port_sub, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    socket.connect("tcp://192.168.0.123:%s" % port_sub)
    socket.subscribe("") 

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

# Configurações de envio e recebimento
port_pub = 6000  # Porta para enviar o áudio
port_sub = 6000  # Porta para receber o áudio

context = zmq.Context()

# Chamar as funções de envio e recebimento em threads separadas
import threading

pub_thread = threading.Thread(target=pub_audio, args=(port_pub, context))
sub_thread = threading.Thread(target=sub_audio, args=(port_sub, context))

pub_thread.start()
time.sleep(1)
sub_thread.start()

# Aguardar as threads terminarem (opcional)
pub_thread.join()
sub_thread.join()
