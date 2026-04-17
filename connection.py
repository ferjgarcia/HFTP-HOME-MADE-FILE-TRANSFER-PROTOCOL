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

            pos_bytes = self.buffer.find(EOL.encode("ascii"))   # Busco el primer \r\n
            actual_buffer  = self.buffer[:pos_bytes]      # extraigo los datos a utilizar del buffer
            self.buffer = self.buffer[pos_bytes+2:] # Recorto el buffer original, saco los datos que uso ahora

            decoded_string = actual_buffer.decode()     # Paso de bytes a string
            argumentos = decoded_string.split()
            cant_argumentos = len(argumentos)   


            ret_inv_com = str(INVALID_COMMAND) + " " + error_messages[INVALID_COMMAND] + EOL     # Comando inválido
            ret_inv_arg = str(INVALID_ARGUMENTS) + " " + error_messages[INVALID_ARGUMENTS] + EOL     # Argumento inválido
            ret_inv_cant_arg = str(BAD_REQUEST) + " " + error_messages[BAD_REQUEST] + EOL     # Comando vacío
            encoded_inv_com = ret_inv_com.encode("ascii")
            encoded_inv_arg = ret_inv_arg.encode("ascii")
            encoded_inv_cant_arg = ret_inv_cant_arg.encode("ascii")

            if cant_argumentos == 1:    
                if argumentos[0] == COMMANDS[0]:  # Es get_file_listing
                    get_file_listing()      # Funciones a implementar
                elif argumentos[0] == COMMANDS[3]:    # Es help
                    help_command()          # Funciones a implementar
                elif argumentos[0] == COMMANDS[4]:    # Es quit
                    quit_command()          # Funciones a implementar
                else:
                    self.s.send(encoded_inv_com)
            elif cant_argumentos == 2:
                if argumentos[0] == COMMANDS[1]:     # Es get_metadata FILENAME
                        get_metadata(argumentos[1])
                else:
                    self.s.send(encoded_inv_com)

            elif 4 <= cant_argumentos <= 5:     
                if argumentos[0] == COMMANDS[2]:
                    try:
                        OFFSET = int(argumentos[2])
                        SIZE = int(argumentos[3])
                    except:
                        self.s.send(encoded_inv_arg)
                        continue
                    # Sigue la estructura get_slice FILENAME OFFSET SIZE [raw]
                    if cant_argumentos == 5 and argumentos[4] == "raw":
                        get_slice(argumentos[1], OFFSET, SIZE, "raw")
                    elif cant_argumentos == 4:
                        get_slice(argumentos[1], OFFSET, SIZE)
                    else:
                        self.s.send(encoded_inv_arg)

                else:
                    self.s.send(encoded_inv_com)
            elif cant_argumentos == 0:
                self.s.send(encoded_inv_cant_arg)
            else:
                self.s.send(encoded_inv_com)

        
        # INSTRUCCIONES DE COMO IMPLEMENTAR DE CLASES
        # Leo entrada, leer hasta que llegue \r\n
        # Me fijo si es un comando
        # Si los parámetros son correctos
        # Ejecuto el comando
        # Mando respuesta
