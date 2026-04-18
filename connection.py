# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import client
from base64 import b64encode

from constants import (
    BAD_EOL,
    BAD_OFFSET,
    BAD_REQUEST,
    CODE_OK,
    COMMANDS,
    CONTENT_LENGTH_PREFIX,
    EOL,
    FILE_NOT_FOUND,
    INTERNAL_ERROR,
    INVALID_ARGUMENTS,
    INVALID_COMMAND,
    error_messages,
    fatal_status,
)


class Connection:
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, sock: socket.socket, directory: str) -> None:
        # FALTA: Inicializar atributos de Connection
        self.__dir__ = directory
        self.s = sock
        self.buffer = b""
        pass

    #get_slice sin raw, abre filename, salta a offset bytes y lee size bytes
    def get_slice(self, filename: str, offset: int, size: int, raw:bool = False) -> None :
        path = self.__dir__ + "/" + filename #directorio base concatenado al nombre del archivo
        
        try:
            with open(path, "rb") as file : # abrir el arhcivo y leerlo en binario "read byte"
                file.seek(0, 2) 
                filesize = file.tell()
                #obtener el tamaño del archivo
                #filesize = 
                #llegar al final del archivo ???
                #seek() es usada para especificar el offset y moverme a la posicion
                #tell() es usada para 
                #f.tell() returns an integer giving the file object’s current position in the file, measured in bytes from the beginning of the file.
                #  To change the file object’s position, use 
                # f.seek(offset, from_what). 
                # The position is computed from adding offset to a reference point; the reference point is selected by the from_what argument. 
                # A from_what value of 0 measures from the beginning of the file, 1 uses the current file position, and 

                # 2 uses the end of the file as the reference point.
                # 
                #  from_what can be omitted and defaults to 0, using the beginning of the file as the reference point. (https://docs.python.org/2/tutorial/inputoutput.html)

                if offset < 0 or size < 0:
                    msg = str(BAD_OFFSET) + " " + error_messages[BAD_OFFSET] + EOL
                    self.s.sendall(msg.encode("ascii")) #sendall manda bytes al cliente -> escribe en la red
                    return
                if offset + size > filesize:
                    msg = str(203) + " " + error_messages[203] + EOL
                    self.s.sendall(msg.encode("ascii")) #sendall manda bytes al cliente -> escribe en la red
                    return
                
                #leer el fragmento
                file.seek(offset) #mueve el cursor hasta el byte del ofset
                data = file.read(size) #lee size bytes y devuelve data bytes

                if not raw:
                    bytesin64 = b64encode(data)
                    #envia por el socket la linea oblig 
                    self.s.sendall(b"0 OK\r\n") 
                    # (b"" transforma a base64 )
                    self.s.sendall(bytesin64 + b"\r\n")

                else: 
                    header = f"Content-Length: {size}\r\n".encode("ascii")
                    # mandar bytes crudos
                    self.s.sendall(b"0 OK\r\n")
                    self.s.sendall(header)
                    self.s.sendall(b"\r\n")
                    self.s.sendall(data) #sin pasarlo a base64

        except FileNotFoundError:
            msg = str(FILE_NOT_FOUND) + " " + error_messages[FILE_NOT_FOUND] + EOL #"<code> <msg>\r\n"
            self.s.sendall(msg.encode("ascii"))
        
        except Exception: #demas fallos son internos
            msg = str(INTERNAL_ERROR) + " " + error_messages[INTERNAL_ERROR] + EOL #"<code> <msg>\r\n"
            self.s.sendall(msg.encode("ascii"))    
        
#'m confused about socket.send() and socket.sendall() functions in Python. As I understand from the documentation send() function uses TCP protocol and sendall() function uses UDP protocol for sending data. I know that TCP is more reliable for most of the Web Applications because we can check which packets are sent and which packets are not. That's why, I think use of send() function can be more reliable rather than sendall() function.
# socket.send is a low-level method and basically just the C/syscall method send(3) / send(2). It can send less bytes than you requested, but returns the number of bytes sent.

# socket.sendall is a high-level Python-only method that sends the entire buffer you pass or throws an exception. It does that by calling socket.send until everything has been sent or an error occurs.

# If you're using TCP with blocking sockets and don't want to be bothered by internals (this is the case for most simple network applications), use sendall.

# And python docs:

# Unlike send(), this method continues to send data from string until either all data has been sent or an error occurs. None is returned on success. On error, an exception is raised, and there is no way to determine how much data, if any, was successfully sent

# Credits to Philipp Hagemeister for brief description I got in the past.

#send() es bajo nivel, puede enviar menos bytes de los q le paso
#es mas fino pero mas propenso a errores
#como usamos TCP, usar send() en este caso podria romper el protocolo HFTP
#el cliente parsea por lineas o por Content-length, se podria enviar solo parte de solo parte de "0 OK\r\n", o parte del base64, o cortar el header en raw
#sendall() es un wrapper sobre send() -> hace el loop para enviar todo 
#o se envia todo o lanza excepcion, pero no devuelve cantidad de Bytes

#send y sendall() usan el mismo protocolo, pero sendall() envia todo o lanza una excepcion. -> send() tiene el problema de que llegue solo 0 OK sin el EOL, rompiendo el parser

#tcp es stream de bytes sin limite de mensaje, y el receptor no sabe donde termina un mensaje y empieza el que le sigue, entonces el protocolo usa una convencion para que el clietne sepa donde dejo de leer -> esto lo llamamos framing

#tenemos dos estratefgias de framing:

#base64 : EL cliente lee hasta encontrar EOL, y hacer esto en base64 garantiza q la salida sean solo caracteres ascii imprimibles; entonces nunca aparece un EOL en medio de los datos codificados, entonces EOL es un delimitador seguro y no es confuso
#el cliente va a recibir hasta que encuentro un EOL (lo va a tener que decodficar)

#en el modo RAW, hacemos framing por content-length (largo del contenido)
#los bytes serian arbitrarios (cualquier byte podria ser EOL en base64 por coincidencia) , entonces usar un delimitador seria confuso para el cliente (mezcla datos con el EOL)
#le avisamos cuantos datos va a recibir de antemanos con content lenght, y el cliente entonces va a leer el header y leer n bytes, sin buscar un delimitador, entonces sin importar lo que haya adentro, lee la cantidad n de bytes y para

#en ascii cada caracter ocupa 1 Byte, pero en utf8, hay caracteres que ocupan mas bytes, entonces podriamos pasar un offset y un tamaño que nos corte en medio un caracter especial
#en modo raw se mandan los bytes crudos, para q el cliente los interprete, y en base64 b64encode opera sobre bytes arbitrarios sin importar si son texto valido o no
#si quisieramos hacer data.decode("utf-8") sobre un fragmento, podriamos obtener un error de decodificacion de unicode. Lo evitamos abriendo el modo en readbynari, y nunca intenta decodificar el contenido, tratandolo siempre como bytes opacos

    
    def handle(self) -> None:
        """
        Atiende eventos de la conexión hasta que termina.
        """
        while True:
            # Leo entrada, leer hasta que llegue \r\n
            while EOL.encode("ascii") not in self.buffer:
                temp_buff = self.s.recv(4096)
                if temp_buff == b"":       # Si recibo vacío, significa que la conexión terminó
                    return
                self.buffer += temp_buff

            pos_bytes = self.buffer.find(EOL.encode("ascii"))   # Busco el primer "\r\n"
            actual_buffer  = self.buffer[:pos_bytes]      # extraigo los datos a utilizar del buffer
            self.buffer = self.buffer[pos_bytes+2:] # Recorto el buffer original, saco los datos que uso ahora

            if b"\n" in actual_buffer:    # Si encunentro un "\n" solo en el comando actual retorno error
                ret_bad_eol = str(BAD_EOL) + " " + error_messages[BAD_EOL] + EOL    
                self.s.send(ret_bad_eol.encode("ascii"))
                return
            
            decoded_string = actual_buffer.decode()     # Paso de bytes a string
            argumentos = decoded_string.split()         # Lista de argumentos
            cant_argumentos = len(argumentos)


            ret_inv_com = str(INVALID_COMMAND) + " " + error_messages[INVALID_COMMAND] + EOL     # Comando inválido
            ret_inv_arg = str(INVALID_ARGUMENTS) + " " + error_messages[INVALID_ARGUMENTS] + EOL     # Argumento inválido
            ret_inv_cant_arg = str(BAD_REQUEST) + " " + error_messages[BAD_REQUEST] + EOL     # Comando vacío
            encoded_inv_com = ret_inv_com.encode("ascii")
            encoded_inv_arg = ret_inv_arg.encode("ascii")
            encoded_inv_cant_arg = ret_inv_cant_arg.encode("ascii")

            if cant_argumentos == 0:      # Se pasó una línea vacía
                self.s.send(encoded_inv_cant_arg)
                return

            if argumentos[0] == COMMANDS[0]:  # Es get_file_listing
                if cant_argumentos == 1:
                    get_file_listing()                          # Funciones a implementar
                else:
                    self.s.send(encoded_inv_arg)        # Se pasaron más argumentos de los necesarios (Repetido en los demás)

            elif argumentos[0] == COMMANDS[3]:    # Es help
                if cant_argumentos == 1:
                    help_command()                              # Funciones a implementar
                else:
                    self.s.send(encoded_inv_arg)

            elif argumentos[0] == COMMANDS[4]:    # Es quit
                if cant_argumentos == 1:
                    quit_command()                              # Funciones a implementar
                else:
                    self.s.send(encoded_inv_arg)

            elif argumentos[0] == COMMANDS[1]:    # Es get_metadata FILENAME
                if cant_argumentos == 2:    
                    get_metadata(argumentos[1]) # Debería poner una comprobación de si esta bien el argumento o se hace en la función?
                else: 
                    self.s.send(encoded_inv_arg)

            elif argumentos[0] == COMMANDS[2]:     
                try:
                    OFFSET = int(argumentos[2])     # Comprobamos si OFFSET y SIZE son números
                    SIZE = int(argumentos[3])
                except:
                    self.s.send(encoded_inv_arg)
                    continue
                # Sigue la estructura get_slice FILENAME OFFSET SIZE [raw]
                if cant_argumentos == 5 and argumentos[4] == "raw":
                    self.get_slice(argumentos[1], OFFSET, SIZE, raw = True)
                elif cant_argumentos == 4:
                    self.get_slice(argumentos[1], OFFSET, SIZE)
                else:
                    self.s.send(encoded_inv_arg)
            else:
                self.s.send(encoded_inv_com)        # Si no existe el comando


        
        # INSTRUCCIONES DE COMO IMPLEMENTAR DE CLASES
        # Leo entrada, leer hasta que llegue \r\n
        # Me fijo si es un comando
        # Si los parámetros son correctos
        # Ejecuto el comando
        # Mando respuesta
