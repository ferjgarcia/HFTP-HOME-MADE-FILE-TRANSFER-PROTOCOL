#!/usr/bin/env python
# encoding: utf-8
# Revisión 2019 (a Python 3 y base64): Pablo Ventura
# Revisión 2014 Carlos Bederián
# Revisión 2011 Nicolás Wolovick
# Copyright 2008-2010 Natalia Bidart y Daniel Moisset
# $Id: server.py 656 2013-03-18 23:49:11Z bc $

import argparse
import socket
import sys
import connection
from constants import DEFAULT_ADDR, DEFAULT_DIR, DEFAULT_PORT


class Server:
    """
    El servidor, que crea y atiende el socket en la dirección y puerto
    especificados donde se reciben nuevas conexiones de clientes.
    """

    def __init__(
        self,
        addr: str = DEFAULT_ADDR,
        port: int = DEFAULT_PORT,
        directory: str = DEFAULT_DIR,
    ) -> None:
        print(f"Serving {directory} on {addr}:{port}.")
        # FALTA: Crear socket del servidor, configurarlo, asignarlo
        # a una dirección y puerto, etc.
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((addr, port))
        self.__dir__ = directory
        self.serverSocket.listen(3)

    def serve(self) -> None:
        """
        Loop principal del servidor. Se acepta una conexión a la vez
        y se espera a que concluya antes de seguir.
        """
        while True:
            pass
            # FALTA: Aceptar una conexión al server, crear una
            # Connection para la conexión y atenderla hasta que termine.
            (clientSocket, addres) = self.serverSocket.accept()
            conn = connection(clientSocket, self.__dir__)
            conn.handle()


def main() -> None:
    """Parsea los argumentos y lanza el server"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p", "--port",
        help="Número de puerto TCP donde escuchar",
        type=int,
        default=DEFAULT_PORT,
    )
    parser.add_argument(
        "-a", "--address",
        help="Dirección donde escuchar",
        default=DEFAULT_ADDR,
    )
    parser.add_argument(
        "-d", "--datadir",
        help="Directorio compartido",
        default=DEFAULT_DIR,
    )
    args = parser.parse_args()
    try:
        server = Server(args.address, args.port, args.datadir)
        server.serve()
    except OSError as e:
        sys.stderr.write(f"Error al iniciar el servidor: {e}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
