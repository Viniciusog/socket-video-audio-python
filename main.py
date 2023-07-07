# SISTEMAS DISTRIBUÍDOS
# Grupo D
# Membros:
# Guilherme Tanaka Carloto
# Vinicius de Oliveira Guimaraes
# Thiago Martins
# Arthur Eugenio Silverio

# Descrição de como executar o programa está no github: 
# https://github.com/Viniciusog/socket-video-python

# Digite pip install -r requirements.txt para instalar as dependências
import sys
import zmq
import time
import threading
import cv2
import base64
import numpy as np
import socket
import pyaudio

# Definição das portas
text_port = 6000
video_port = 6001
audio_port = 6002

# Indica se estamos saindo da aplicação ou não
# É ativado quando digitamos #quit no terminal
EXIT = 0

# Pega o endereço do computador na rede local
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Tenta se conectar a um servidor DNS
    s.connect(("8.8.8.8", 80))
    # Obtém o endereço IP local do socket
    local_ip = s.getsockname()[0]
    return local_ip

# Envia uma mensagem indicando que o socket atual está saindo.
# É que quem esteja ouvindo um socket, consiga tratar no caso da saída do mesmo.
# Ex: Caso um socket que estamos ouvindo pare de compartilhar a Webcam, iremos remover a janela dele.
def quit_socket(socket):
    topic = "quit-" + get_local_ip()
    to_send = b"%s %s" % (topic.encode(), b"Nothing")
    socket.send(to_send)

# Função que representa a thread para inserir texto no chat.
# Os textos são publicados na porta text_port = 6000
def pub_text(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port_pub)

    topic = "*" + get_local_ip()
    print("|---------------Chat---------------|")
    while True:
        message = input()
        # Significa que estamos saindo/parando de publicar texto.
        if message == "#quit":
            quit_socket(socket)
            global EXIT
            EXIT = 1
            break
        socket.send(b"%s %s" % (topic.encode(), message.encode()))

    print("Saindo pub_text")
    socket.close()

# Função que representa a thread para ouvir textos.
# Iremos conectar com os IP's passados como parâmetro, ouvindo na porta text_port = 6000
def sub_text(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)
    # Conecta em todos os IP's recebidos como parâmetro, passando a porta text_port = 6000
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, int(text_port)))
        socket.subscribe("*" + ip)
        socket.subscribe("quit-" + ip)

    while True:
        string = socket.recv()
        # As informações recebidas contém o tópico e os dados úteis (texto digitado por um usuário)
        topic, messagedata = string.split(b" ", 1)

        # Se recebermos uma mensagem de saída, então mostramos que o usuário está saindo.
        if topic.decode().startswith("quit"):
            # Quando um usuário sai, iremos receber uma mensagem com o tópico quit-IP_DO_USUARIO
            ip_user_quitting = topic.decode().split("-")[1]
            print("Usuário %s saiu do canal de texto." % (ip_user_quitting))
            # Se o EXIT = 1, então significa que nós mesmos estamos saindo
            if EXIT:
                break
            continue

        # Imprimi no terminal dizendo que recebeu a mensagem de um usuário (mostra o ip do usuário)
        print("%s: %s\n" % (topic.decode(), messagedata.decode()))

    print("Saindo sub_text")
    socket.close()

# Função que representa a thread de publicação de vídeo da Webcam
def pub_video(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)

    socket.bind("tcp://*:%s" % port_pub)

    # Inicia webcam
    camera = cv2.VideoCapture(0)
    quitting_key_q = 0

    while not EXIT:
        # Pega os frames da câmera
        (grabbed, frame) = camera.read()
        frame = cv2.resize(frame, (320, 240))
        encoded, buffer = cv2.imencode(".jpg", frame)

        # Cria o tópico da mensagem
        topic = "*" + get_local_ip()

        # Codifica o nosso buffer e envia através do socket
        to_send = b"%s " % (topic.encode())
        buffer_encoded = base64.b64encode(buffer)
        to_send += buffer_encoded
        socket.send(to_send)

        # Mostra a imagem da nossa Webcam em uma janela chamada Webcam
        cv2.imshow("Webcam", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            quitting_key_q = 1
            # ? Colocar exit = 1 aqui ??
            quit_socket(socket)
            break

    camera.release()
    
    # Se estamos apertando q para fechar a janela, precisamos indicar que estamos 
    # parando de compartilhar a tela, para que esse evento seja tratado pelos ouvintes.
    if not quitting_key_q:
        quit_socket(socket)

    cv2.destroyWindow("Webcam")
    socket.close()
    print("Saindo pub_video")

# Função que representa a thread para "ouvir" o vídeo de outros usuários.
def sub_video(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)

    # Conecta nos IP's passados como parâmetro, incluindo a porta video_port = 6002
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%d" % (ip, video_port))
        # Se increve no tópico com o *IP para conseguir saber qual nome colocar nas 
        # janelas de vídeo e quais janelas fechar.
        topic = "*" + ip
        socket.subscribe(topic)
        # Se increve no tópico quit-IP para conseguir saber quando um usuário para de compartilhar vídeo.
        quit_topic = "quit-" + ip
        socket.subscribe(quit_topic)

    # Se digitarmos q na webcam, iremos executar o quitting, mas o exit aidna será 0.
    # o exit ainda será 0. Em seguida, quando
    while True:
        print("A")
        string = socket.recv()
        print("B")
        topic, frame_encoded = string.split()

        # Significa que um determinado usuário está saindo
        if topic.decode().startswith("quit"):
            ip_user_quitting = topic.decode().split("-")[1]
            print(
                "Usuário %s saiu do canal de vídeo. Removendo janela.."
                % (ip_user_quitting)
            )
            cv2.destroyWindow(ip_user_quitting)
            # Se EXIT = 1, então somos nós mesmos que estamos saindo
            if EXIT:
                break
            continue
        
        # Decodifica um frame
        img = base64.b64decode(frame_encoded)
        npimg = np.frombuffer(img, dtype=np.uint8)
        source = cv2.imdecode(npimg, 1)
        
        # Mostra a imagem recebida na tela, inserindo o nome da janela como sendo o nome do usuário que enviou a imagem
        cv2.imshow(str(topic.decode()[1:]), source)
        
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Tecla q Pressionada. Removendo janela da minha Webcam..")
            break
    
    socket.close()
    print("Saindo sub_video")


# Função que representa a thread para publicação de áudio
def pub_audio(port_pub, zmq_context):
    socket = zmq_context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port_pub)

    # Configurações do áudio
    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    # Criação do stream de áudio
    stream = my_audio.open(
        format=format,
        channels=channels,
        rate=sample_rate,
        input=True,
        frames_per_buffer=frames_per_buffer,
    )

    while not EXIT:
        # Realiza a capturação do áudio e envia através do socket pub
        data = stream.read(frames_per_buffer)
        to_send = b"%s %s" % (b"*", data)
        socket.send(to_send)

    # Quando digitarmos #quit no terminal, o nosso socket irá parar de publicar informações, incluindo parar de publicar áudio
    quit_socket(socket)
    socket.close()
    print("Saindo pub_audio")

# Função que representa a thread quue vai ficar "ouvindo" áudio de outros usuários.
def sub_audio(ips_to_connect, zmq_context):
    socket = zmq_context.socket(zmq.SUB)

    # Conecta o socket nos IP's recebidos como parâmetro
    for ip in ips_to_connect:
        socket.connect("tcp://%s:%s" % (ip, audio_port))
        # Se inscreve no tópico quit-IP para tratar quando um usuário para de compartilhar áudio
        socket.subscribe("quit-" + ip)

    socket.subscribe("*")

    # Configuração do áudio
    my_audio = pyaudio.PyAudio()
    sample_rate = 44100
    format = pyaudio.paInt16
    channels = 1
    frames_per_buffer = 1024

    # Criação do stream de áudio
    stream = my_audio.open(
        format=format,
        channels=channels,
        rate=sample_rate,
        output=True,
        frames_per_buffer=frames_per_buffer,
    )

    while True:
        # Recebe as informações
        string = socket.recv()

        # Separa o tópico dos dados de áudio
        topic, data = string.split(b" ", 1)

        # Significa que algum usuário está saindo
        if topic.decode().startswith("quit"):
            ip_user_quitting = topic.decode().split("-")[1]
            print("Usuário %s saiu do canal de áudio." % (ip_user_quitting))
            # Se EXIT = 1, então somos nós mesmos que estamos saindo
            if EXIT:
                break
            continue
        
        # Envia o áudio que recebemos para a saída de áudio (por exemplo um fone de ouvido)
        stream.write(data)
    
    # Fecha o socket
    socket.close()
    print("Saindo sub_audio")


# Pegando os parâmetros passados quando executar o arquivo
strArgv = ""
for element in sys.argv[1:]:
    strArgv += str(element) + " "
strArgv = strArgv.strip()

# Pega os nós que devemos conectar a partir dos parâmetros passados na execução do arquivo
nodes = strArgv.split("-node ")
print("Nós para conectar:")
for i in range(1, len(nodes) - 1):
    nodes[i] = nodes[i].strip()

nodes = nodes[1:]
print(nodes)

# Criando contexto para as threads
context = zmq.Context()

# Cria e inicializa a thread de publicação de texto
thread_pub = threading.Thread(target=pub_text, args=(text_port, context))
thread_pub.start()

# Cria e inicializa a thread que vai receber texto de outros usuários
thread_sub = threading.Thread(target=sub_text, args=(nodes, context))
thread_sub.start()

# Cria e inicializa a thread de publicação de vídeo
thread_pub_video = threading.Thread(target=pub_video, args=(video_port, context))
thread_pub_video.start()

# Cria e inicializa a thread que vai receber vídeo de outros usuários
thread_sub_video = threading.Thread(target=sub_video, args=(nodes, context))
thread_sub_video.start()

# Cria e inicializa a thread de publicação de áudio
thread_pub_audio = threading.Thread(target=pub_audio, args=(audio_port, context))
thread_pub_audio.start()
time.sleep(1)

# Cria e inicializa a thread que vai receber áudio de outros usuários
thread_sub_audio = threading.Thread(target=sub_audio, args=(nodes, context))
thread_sub_audio.start()
