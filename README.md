# socket-video-python

As portas e texto, vídeo e áudio foram padronizadas. <br>
Porta de texto = 6000
Porta de vídeo = 6001
Porta de áudio = 6002

Para rodar o arquivo, ouvindo o usuário 192.168.0.114, digite:
```
py main.py -node 192.168.0.114
```

Para rodar o arquivo somente com os subs (Apenas ouvir informações, sem publicar), ouvindo os usuários 192.168.0.114 e 192.168.0.115, digite:
```
py main.py -sub -node 192.168.0.114 -node 192.168.0.115
```
Se quiser ouvir outros usuários, basta adicionar mais ```-node ip_do_usuario``` na hora de executar o arquivo main.py
