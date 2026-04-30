# Lab 2 — HFTP: Home-made File Transfer Protocol

Implementamos un servidor de archivos en Python 3 que habla el protocolo **HFTP** sobre TCP.
El servidor acepta conexiones de múltiples clientes simultáneamente (hilos), responde comandos
como `get_file_listing`, `get_metadata` y `get_slice`, y maneja errores sin caerse.

`get_slice` soporta dos modos de transferencia:

- **Base64**: el fragmento viaja codificado en una línea ASCII delimitada por `\r\n`.
- **Raw**: los bytes viajan tal cual, con `Content-Length` indicando cuántos leer.

Como cierre, demostramos HFTP operando sobre la red **Tor** — servidor publicado como
servicio oculto `.onion` y cliente accediendo vía `torsocks` — sin modificar una línea del protocolo.

---

## Video

[![Portada del video](https://img.youtube.com/vi/Oul5hkSJsmk/maxresdefault.jpg)](https://youtu.be/Oul5hkSJsmk)

---

## Integrantes

- BARRAUD, Emma
- CASTILLO, Agustín
- GARCÍA, Fernando
- RÍOS, L Julían