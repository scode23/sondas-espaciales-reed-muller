"""Código Golay binario extendido [24,12,8], usado por Voyager.

Codifica 12 bits por palabra y corrige hasta 3 errores. Cada píxel se guarda
como un byte seguido de cuatro bits cero; al reconstruir se conserva el byte.
"""
import numpy as np

N, K, DISTANCIA, T = 24, 12, 8, 3


def _codificar_mensajes(mensajes):
    """Codificador sistemático del Golay cíclico [23,12,7] extendido."""
    salida = np.zeros((len(mensajes), 24), dtype=np.uint8)
    # g(x) = x^11 + x^9 + x^7 + x^6 + x^5 + x + 1
    potencias = (11, 9, 7, 6, 5, 1, 0)
    for fila, mensaje in enumerate(mensajes):
        resto = np.zeros(23, dtype=np.uint8)
        resto[:12] = mensaje
        for i in range(12):
            if resto[i]:
                for potencia in potencias:
                    resto[i + 11 - potencia] ^= 1
        salida[fila, :12] = mensaje
        salida[fila, 12:23] = resto[12:]
        salida[fila, 23] = salida[fila, :23].sum() % 2
    return salida


_MENSAJES = np.array([[(i >> (11 - j)) & 1 for j in range(K)] for i in range(1 << K)], dtype=np.uint8)
_CODIGOS = _codificar_mensajes(_MENSAJES)
_CODIGOS_BIPOLARES = _CODIGOS.astype(np.float32) * 2 - 1


def preparar(imagen):
    """Empaqueta cada píxel en 12 bits: 8 de intensidad y 4 bits de relleno."""
    pixeles = imagen.reshape(-1).astype(np.uint8)
    bloques = np.zeros((len(pixeles), 12), dtype=np.uint8)
    bloques[:, :8] = np.unpackbits(pixeles[:, None], axis=1)
    return imagen.shape, bloques


def transmitir(bloques, probabilidad, rng):
    """Codifica los bloques y aplica el canal binario simétrico."""
    palabras = _codificar_mensajes(bloques)
    ruido = (rng.random(palabras.shape) < probabilidad).astype(np.uint8)
    return palabras ^ ruido


def decodificar(recibidas):
    """Decodifica por máxima correlación con las 4096 palabras válidas."""
    estimadas = []
    for inicio in range(0, len(recibidas), 2_000):
        lote = recibidas[inicio:inicio + 2_000].astype(np.float32) * 2 - 1
        indices = np.argmax(lote @ _CODIGOS_BIPOLARES.T, axis=1)
        estimadas.append(_MENSAJES[indices])
    return np.concatenate(estimadas, axis=0)


def reconstruir(bloques, forma):
    """Recupera los ocho bits de intensidad de cada bloque."""
    pixeles = np.packbits(bloques[:, :8], axis=1).reshape(-1)
    return pixeles.reshape(forma)
