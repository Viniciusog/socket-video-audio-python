# socket-video-python

As portas de texto, vídeo e áudio foram padronizadas. <br>
Porta de texto = 6000. <br>
Porta de vídeo = 6001. <br>
Porta de áudio = 6002. <br>

Para pegar o IP do seu computador na rede, você pode digitar no terminal ```ipconfig``` <br>
Com isso, vai aparecer o texto abaixo no terminal, basta olhar o que está em ```Adaptador de Rede sem Fio Wi-Fi -> Endereço IPv4:```
```
Adaptador de Rede sem Fio Wi-Fi:
   Endereço IPv4. . . . . . . .  . . . . . . . : seu_ip_vai_estar_aqui
```

## Requisitos

Para instalar as dependências, digite: <br>
```pip install -r requirements.txt```

## Executar programa

Para rodar o arquivo, ouvindo o usuário 192.168.0.114, digite:
```
py main.py -node 192.168.0.114
```

Para rodar o arquivo, ouvindo os usuários 192.168.0.114 e 192.168.0.68, digite:

```
py main.py -node 192.168.0.114 -node 192.168.0.68
```
Se quiser ouvir outros usuários, basta adicionar mais ```-node ip_do_usuario``` na hora de executar o arquivo main.py

### Fazer usuário sair/parar de publicar dados

Quando estiver rodando um usuário e quiser fazer ele sair/parar de publicar dados, digite no chat <br>
o seguinte comando especial que criamos: ```#quit```

Com isso, o seu usuário irá parar todos os pubs, notificando todos os outros usuários que estavam escutando ele.
Em seguida, basta terminar o processo desse seu usuário.

