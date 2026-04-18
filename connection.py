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
    def get_slice(self, filename : str, offset : int, size : int) -> None :
        path = self.__dir__ + "/" + filename #directorio base concatenado al nombre del archivo
        
        try:
            with (path, "rb") as file : # leer el binario "read byte"
                #obtener el tamaño del archivo
                #filesize = 
                #llegar al final del archivo ???

                if offset < 0 or size < 0:
                    #bad offset
                    return
                if offset + size > filesize:
                    #error 203 posicion inexistente
                    return
                
                #leer el fragmento
                file.seek(offset) #mueve el cursor hasta el byte del ofset
                data = file.read(size) #lee size bytes y devuelve data bytes

                bytesin64 = b64encode(data)

                #envia por el socket la linea oblig 
                self.s.send(b"0 OK\r\n") 
                # (b"" transforma a base64 )
                self.s.send(bytesin64 + b"\r\n")

        except FileNotFoundError :
            # msg = mensaje de error
             self.s.send(msg.encode("ascii"))
        
        except Exception :
            # msg = mensaje de error
             self.s.send(msg.encode("ascii"))    
        
    
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
                    self.get_slice(argumentos[1], OFFSET, SIZE, "raw")
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
