# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Copyright 2014 Carlos Bederián
# $Id: connection.py 455 2011-05-01 00:32:09Z carlos $

import socket
from base64 import b64encode
import os
import logging

from constants import (
    BAD_EOL,
    BAD_OFFSET,
    BAD_REQUEST,
    CODE_OK,
    COMMANDS,
    # CONTENT_LENGTH_PREFIX
    EOL,
    FILE_NOT_FOUND,
    INTERNAL_ERROR,
    INVALID_ARGUMENTS,
    INVALID_COMMAND,
    error_messages,
    # fatal_status
)


class Connection:
    """
    Conexión punto a punto entre el servidor y un cliente.
    Se encarga de satisfacer los pedidos del cliente hasta
    que termina la conexión.
    """

    def __init__(self, sock: socket.socket, directory: str) -> None:
        # FALTA: Inicializar atributos de Connection
        self.directory = directory
        self.s = sock
        self.buffer = b""
        self._connected = False

    def get_slice(
        self, filename: str, offset: int, size: int, raw: bool = False
    ) -> None:
        """
        envia SIZE bytes del archivo FILENAME a partir de OFFSET.

        metodos de framing:
        - base64 (raw=False): el fragmento se codifica en base64 y se envia
          como una sola linea ascii terminada en \\r\\n. el cliente lee hasta
          ese delimitador y decodifica. funciona porque base64 nunca produce
          los bytes 0x0D ni 0x0A en su salida

        - raw (raw=True): se envia una cabecera Content-Length con el num
          exacto de bytes, luego una linea vacia y despues los bytes
          del archivo.  \\r\\n no se puede usar
          porque el archivo puede contener esos mismos bytes como datos
        """

        # construir el path y veo que no sesalga del directorio base
        if ".." in filename or "/" in filename:
            msg = str(FILE_NOT_FOUND) + " " + \
                error_messages[FILE_NOT_FOUND] + EOL
            self.s.sendall(msg.encode("ascii"))
            return

        path = self.directory + "/" + filename

        try:
            with open(
                path, "rb"
            ) as file:  # abrir el arhcivo y leerlo en binario "read byte"
                file.seek(0, 2)  # me muevo al final del archivo (2)
                filesize = file.tell()  # leo la posicion

                if offset < 0 or size < 0:
                    msg = str(BAD_OFFSET) + " " + \
                        error_messages[BAD_OFFSET] + EOL
                    self.s.sendall(
                        msg.encode("ascii")
                    )  # sendall manda bytes al cliente -> escribe en la red
                    return
                if offset + size > filesize:
                    msg = str(203) + " " + error_messages[203] + EOL
                    self.s.sendall(
                        msg.encode("ascii")
                    )  # sendall manda bytes al cliente -> escribe en la red
                    return

                # leer el fragmento
                file.seek(offset)  # mueve el cursor hasta el byte del ofset
                data = file.read(size)  # lee size bytes y devuelve data bytes

                if not raw:
                    # en base64, framinf por el delimitador EOL
                    # b64encode nos garantiza salida ascii pura, entonces
                    # el eol es seguro (como delimitador de finlinea)
                    bytesin64 = b64encode(data)
                    # envia por el socket la linea oblig
                    self.s.sendall(b"0 OK\r\n")
                    # (b"" transforma a base64 )
                    self.s.sendall(bytesin64 + b"\r\n")

                else:
                    # en raw, el framing es por longitud
                    # leemos content-lenght bytes del cuerpo
                    header = f"Content-Length: {size}\r\n".encode("ascii")
                    # mandar bytes crudos
                    self.s.sendall(b"0 OK\r\n")
                    self.s.sendall(header)
                    self.s.sendall(b"\r\n")  # linea vacia = fin de cabeceras
                    self.s.sendall(data)  # sin pasarlo a base64

        except FileNotFoundError:
            msg = (
                str(FILE_NOT_FOUND) +
                " " +
                error_messages[FILE_NOT_FOUND] +
                EOL)  # "<code> <msg>\r\n"
            self.s.sendall(msg.encode("ascii"))

        except Exception:  # demas fallos son internos
            msg = (
                str(INTERNAL_ERROR) +
                " " +
                error_messages[INTERNAL_ERROR] +
                EOL)  # "<code> <msg>\r\n"
            self.s.sendall(msg.encode("ascii"))

    def handle(self) -> None:
        #self.s.settimeout(10.0)
        print("DEBUG: Iniciando manejo de conexión...")
        self._connected = True
        while self._connected:
            try:
                # Busca saltos de linea
                if b"\n" in self.buffer:
                    pos = self.buffer.find(b"\n")

                    # Valida BAD_EOL
                    if pos == 0 or self.buffer[pos - 1] != ord("\r"):
                        ret = str(BAD_EOL) + " " + \
                            error_messages[BAD_EOL] + EOL
                        self.s.sendall(ret.encode("ascii"))

                        self.s.close()
                        return

                    linea = self.buffer[:pos - 1]
                    self.buffer = self.buffer[pos + 1:]

                    self.process_command(
                        linea.decode(
                            "ascii", errors="ignore"))
                    continue

                # Recepcion de datos
                temp_buff = self.s.recv(4096)

                if temp_buff == b"":
                    self.s.close()
                    return

                self.buffer += temp_buff

            except socket.timeout:
                continue
            except Exception:
                self.s.close()
                return

    def process_command(self, decoded_string: str) -> None:
        """
        He movido la lógica de procesamiento aquí para limpiar el handle().
        """
        argumentos = decoded_string.split()
        cant_argumentos = len(argumentos)

        ret_inv_com = (
            str(INVALID_COMMAND) + " " + error_messages[INVALID_COMMAND] + EOL
        )  # Comando inválido
        ret_inv_arg = (
            str(INVALID_ARGUMENTS) +
            " " +
            error_messages[INVALID_ARGUMENTS] +
            EOL)  # Argumento inválido
        ret_inv_cant_arg = (
            str(BAD_REQUEST) + " " + error_messages[BAD_REQUEST] + EOL
        )  # Comando vacío
        encoded_inv_com = ret_inv_com.encode("ascii")
        encoded_inv_arg = ret_inv_arg.encode("ascii")
        encoded_inv_cant_arg = ret_inv_cant_arg.encode("ascii")

        # logging.info("Request: get_metadata %s", decoded_string)
        if cant_argumentos == 0:  # Se pasó una línea vacía
            self.s.send(encoded_inv_cant_arg)
            return

        if argumentos[0] == COMMANDS[0]:  # Es get_file_listing
            if cant_argumentos == 1:
                logging.info("Request: get_file_listing")
                self.get_file_listing()

            else:
                # Se pasaron más argumentos de los necesarios (Repetido en los
                # demás)
                self.s.send(encoded_inv_arg)

        elif argumentos[0] == COMMANDS[3]:  # Es help
            logging.info("Request: help")
            if cant_argumentos == 1:
                self.help()
            else:
                self.s.send(encoded_inv_arg)

        elif argumentos[0] == COMMANDS[4]:  # Es quit
            logging.info("Request: quit")
            if cant_argumentos == 1:
                self.quit()
                return
            else:
                self.s.send(encoded_inv_arg)

        elif argumentos[0] == COMMANDS[1]:    # Es get_metadata FILENAME
            if cant_argumentos == 2:
                logging.info("Request: get_metadata %s", decoded_string)
                self.get_metadata(argumentos[1])
            else:
                self.s.send(encoded_inv_arg)

        elif argumentos[0] == COMMANDS[2]:  # get_slice
            try:
                OFFSET = int(argumentos[2])
                SIZE = int(argumentos[3])
            except (ValueError, IndexError):
                # Corregido: usamos return en lugar de continue
                self.s.send(encoded_inv_arg)
                return

            # Sigue la estructura get_slice FILENAME OFFSET SIZE [raw]
            if cant_argumentos == 5 and argumentos[4] == "raw":
                logging.info("Request: get_slice %s", decoded_string)
                self.get_slice(
                    argumentos[1],
                    OFFSET,
                    SIZE,
                    True)  # Corregí 'raw' a True
            elif cant_argumentos == 4:
                self.get_slice(argumentos[1], OFFSET, SIZE)
            else:
                self.s.send(encoded_inv_arg)
        else:
            self.s.send(encoded_inv_com)

    def get_file_listing(self) -> None:
        """
        Sin argumentos.
        Obtiene la lista de archivos disponibles.
        Payload: nombres de archivos, uno por línea, línea vacía \r\n indica fin.
        Respuesta: 0 OK + \r\n + nombres + \r\n.
        """

        result = os.listdir(self.directory)
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

    def get_metadata(self, file: str) -> None:
        """
        Un argumento FILENAME.
        Payload en éxito: una línea con el tamaño en bytes (decimal ASCII) + \r\n.
        Respuesta: 0 OK + \r\n + tamaño + \r\n.
        """

        ret_file_not_found = str(FILE_NOT_FOUND) + \
            " " + error_messages[FILE_NOT_FOUND] + EOL
        encoded_file_not_found = ret_file_not_found.encode("ascii")
        list_file = os.listdir(self.directory)
        if file in list_file:
            path = os.path.join(self.directory, file)
            size = os.path.getsize(path)
            ret = str(CODE_OK) + " " + error_messages[CODE_OK] + EOL
            ret_size = str(size) + EOL
            self.s.send(ret.encode("ascii"))
            self.s.send(ret_size.encode("ascii"))
        else:
            self.s.send(encoded_file_not_found)
        return None

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
        self._connected = False

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
