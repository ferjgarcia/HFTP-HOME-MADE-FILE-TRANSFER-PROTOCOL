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
            while b"\r\n" not in self.buffer:
                temp_buff = self.s.recv(4096)
                if temp_buff == b"":       # Si recibo vacío, significa que la conexión terminó
                    break   # A IMPLEMENTAR: Salir del ciclo while externo también
                self.buffer += temp_buff   # A IMPLEMENTAR: Debo buscar el primer \r\n, no arbitrariamente.
            # A IMPLEMENTAR: Recortar el buffer (Eliminar comando usado) al final de la vuelta del ciclo while

            decoded_string = self.buffer.decode()
            cant_argumentos = len(decoded_string[:len(decoded_string)-2].split())   # A IMPLEMENTAR: Dudosa forma de separar argumentos

            ret_inv_com = str(INVALID_COMMAND) + " " + error_messages[INVALID_COMMAND] + "\r\n"     # Comando inválido
            encoded_inv_com = ret_inv_com.encode("ascii")

            # A IMPLEMENTAR: la variable entrada me quedó de antes, solía ser la primera palabra dentro del flujo que entró
            if cant_argumentos == 1:    
                if entrada == COMMANDS[0]:  # Es get_file_listing
                    # A IMPLEMENTAR: Ejecuto el comando
                elif entrada == COMMANDS[3]:    # Es help
                    # A IMPLEMENTAR: Ejecuto el comando
                elif entrada == COMMANDS[4]:    # Es quit
                    # A IMPLEMENTAR: Ejecuto el comando
                else:
                    self.s.send(encoded_inv_com)
            elif cant_argumentos == 2:
                if entrada.split()[0] == COMMANDS[1]:     # Es get_metadata
                    # A IMPLEMENTAR: ver si tiene argumentos válidos y ejecutar el comando
                else:
                    self.s.send(encoded_inv_com)

            elif cant_argumentos == 3 or cant_argumentos == 4:     
                if entrada.split()[0] == COMMANDS[2]:   # Es get_slice
                    # A IMPLEMENTAR: ver si tiene argumentos válidos y ejecutar el comando
                else:
                    self.s.send(encoded_inv_com)        
            else:
                self.s.send(encoded_inv_com)

        
        # INSTRUCCIONES DE COMO IMPLEMENTAR DE CLASES
        # Leo entrada, leer hasta que llegue \r\n
        # Me fijo si es un comando
        # Si los parámetros son correctos
        # Ejecuto el comando
        # Mando respuesta

        pass
