import zmq
import pyaudio
import time

def show_devices():
    my_audio = pyaudio.PyAudio()

    for i in range(my_audio.get_device_count()):
        info = my_audio.get_device_info_by_index(i)
        print(f"Device {i}: {info['name']}")
        print(f"Device defaultSampleRate: {info['defaultSampleRate']}")

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

def sub_audio(ips_to_connect, port_sub, zmq_context):
    """ Device 3: Alto-falantes (Realtek(R) Audio    
    Device defaultSampleRate: 44100.0
    Device 4: Fones de ouvido (Realtek(R) Aud    
    Device defaultSampleRate: 44100.0 """
    socket = zmq_context.socket(zmq.SUB)
    for ip in ips_to_connect:
        print("Conectando em %s" % ip)
        socket.connect("tcp://%s:%s" % (ip, port_sub))
    
    socket.subscribe("*") 

    show_devices()

    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    stream = my_audio.open(format=format, channels=channels, rate=sample_rate, output=True, frames_per_buffer=frames_per_buffer, output_device_index=None)

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

ips_to_connect = ['192.168.0.123', '192.168.0.124']

pub_thread = threading.Thread(target=pub_audio, args=(port_pub, context))
sub_thread = threading.Thread(target=sub_audio, args=(ips_to_connect, port_sub, context))

pub_thread.start()
time.sleep(1)
sub_thread.start()

# Aguardar as threads terminarem (opcional)
pub_thread.join()
sub_thread.join()
