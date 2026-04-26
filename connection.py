# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
import client
from base64 import b64encode
import os
import logging

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
                    logging.info("Request: get_file_listing")
                    self.get_file_listing()                          # Funciones a implementar
                    
                else:
                    self.s.send(encoded_inv_arg)        # Se pasaron más argumentos de los necesarios (Repetido en los demás)

            elif argumentos[0] == COMMANDS[3]:    # Es help
                if cant_argumentos == 1:
                    self.help()                              # Funciones a implementar
                else:
                    self.s.send(encoded_inv_arg)

            elif argumentos[0] == COMMANDS[4]:    # Es quit
                if cant_argumentos == 1:
                    self.quit()                              # Funciones a implementar
                    return
                else:
                    self.s.send(encoded_inv_arg)

            elif argumentos[0] == COMMANDS[1]:    # Es get_metadata FILENAME
                if cant_argumentos == 2:    
                    logging.info("Request: get_metadata %s", decoded_string)
                    self.get_metadata(argumentos[1]) # Debería poner una comprobación de si esta bien el argumento o se hace en la función?
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

    def get_file_listing (self) -> None:
        result = os.listdir(self.__dir__)
        ret_ok = str(CODE_OK) + " " + error_messages[CODE_OK] + EOL
        encoded_ret_ok = ret_ok.encode("ascii")
        self.s.send(encoded_ret_ok)
        for nombre_archivo in result:
            res = nombre_archivo + EOL
            encoded_res = res.encode("ascii")
            self.s.send(encoded_res)
        final = EOL
        encoded_final = final.encode("ascii")
        self.s.send(encoded_final)
        return None
    
    def get_metadata (self, file: str) -> None:
        ret_file_not_found = str(FILE_NOT_FOUND) + " " + error_messages[FILE_NOT_FOUND] + EOL
        encoded_file_not_found = ret_file_not_found.encode("ascii")
        list_file = os.listdir(self.__dir__)
        if file in list_file:
            path = os.path.join(self.__dir__, file)
            size = os.path.getsize(path)
            ret = str(CODE_OK) + " " + error_messages[CODE_OK] + EOL
            ret_size = str(size) + EOL
            self.s.send(ret.encode("ascii"))
            self.s.send(ret_size.encode("ascii"))
        else: 
            self.s.send(encoded_file_not_found)
        return None
        
        # INSTRUCCIONES DE COMO IMPLEMENTAR DE CLASES
        # Leo entrada, leer hasta que llegue \r\n
        # Me fijo si es un comando
        # Si los parámetros son correctos
        # Ejecuto el comando
        # Mando respuesta

    def quit(self) -> None:
        """
        Sin argumentos.
        Termina la conexión.
        El servidor responde 0 OK y cierra la conexión.
        Sin payload.
        """
        msg = str(CODE_OK) + " " + error_messages[CODE_OK] + EOL
        encoded_msg = msg.encode("ascii")
        self.s.send(encoded_msg)
        self.s.close()  # Cerramos la conexión

    def help(self) -> None:
        """
        Lista los comandos disponibles (uno por línea, fin con línea vacía \r\n).
        Facilita pruebas con telnet y depuración.
        Respuesta: 0 OK + \r\n + nombres de comandos + \r\n.
        """
        comms = EOL.join(COMMANDS) + EOL
        msg = str(CODE_OK) + " " + error_messages[CODE_OK] + EOL + comms + EOL
        encoded_msg = msg.encode("ascii")
        self.s.send(encoded_msg)
