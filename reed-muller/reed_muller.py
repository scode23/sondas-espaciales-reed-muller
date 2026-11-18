"""Funciones del código Reed–Muller RM(1,5), usado por Mariner 9.

Cada píxel se representa con 6 bits y se codifica en una palabra de 32 bits.
La distancia mínima es 16, así que se corrigen hasta 7 errores por palabra.
"""
import numpy as np

N, K, DISTANCIA, T = 32, 6, 16, 7
_G = np.array([
    [1] * 32,
    [0] * 16 + [1] * 16,
    ([0] * 8 + [1] * 8) * 2,
    ([0] * 4 + [1] * 4) * 4,
    ([0] * 2 + [1] * 2) * 8,
    [0, 1] * 16,
], dtype=np.uint8)
_MENSAJES = np.array([[(i >> (5 - j)) & 1 for j in range(K)] for i in range(64)], dtype=np.uint8)
_CODIGOS = (_MENSAJES @ _G) % 2
_CODIGOS_BIPOLARES = _CODIGOS.astype(np.float32) * 2 - 1


def preparar(imagen):
    """Cuantiza una imagen gris a 6 bits y la convierte en bloques de mensaje."""
    forma = imagen.shape
    pixeles = (imagen.reshape(-1).astype(np.uint8) >> 2)
    bits = np.unpackbits(pixeles[:, None], axis=1)[:, 2:]
    return forma, bits


def transmitir(bits, probabilidad, rng):
    """Codifica los bloques y aplica el canal binario simétrico."""
    palabras = (bits @ _G) % 2
    ruido = (rng.random(palabras.shape) < probabilidad).astype(np.uint8)
    return palabras ^ ruido


def decodificar(recibidas):
    """Busca la palabra válida de mínima distancia mediante correlación."""
    estimadas = []
    for inicio in range(0, len(recibidas), 100_000):
        lote = recibidas[inicio:inicio + 100_000].astype(np.float32) * 2 - 1
        indices = np.argmax(lote @ _CODIGOS_BIPOLARES.T, axis=1)
        estimadas.append(_MENSAJES[indices])
    return np.concatenate(estimadas, axis=0)


def reconstruir(bits, forma):
    """Reconstruye píxeles de 8 bits a partir de sus 6 bits más significativos."""
    valores = bits.astype(np.uint8) @ (2 ** np.arange(5, -1, -1))
    return (valores.reshape(forma) * 4).astype(np.uint8)
