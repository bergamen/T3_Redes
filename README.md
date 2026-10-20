# TCP stop and wait
Se maneja un sistema de segmentos donde el tipo se maneja simulando una mapa de bits:
- SYN = 1
- ACK = 2
- FIN = 4
Para hacer perdidas, se creo una clase SOCK que hereda de socket, la cual su funcion sendto tiene un probabilidad de no hacer nada
Para manejar el caso borde, si connect detecta que no es un ack pero corresponde a la secuencia entonces la guarda y la envia a la funcion recv
Para manejar los tamaños de los buffer en recv, este le manda al cliente cuanto de las datos consumio para que el cliente pueda mandar datos que envio, pero que no fueron consumidos 
