"""
Núcleo del proyecto: transmisión de una imagen con el código Reed-Muller RM(1,5)
(el de la sonda Mariner 9): cada píxel de 6 bits se codifica en una palabra de 32 bits.

Parámetros del código: [n, k, d] = [32, 6, 16]
  - corrige t = (d-1)//2 = 7 errores por palabra
  - tasa R = k/n = 6/32

Este módulo NO tiene interfaz ni gráficas: solo la lógica, para poder
reutilizarla desde la GUI y desde los experimentos.
"""
import numpy as np
from math import comb
from PIL import Image

# ----------------------------------------------------------------------
# Constantes del código (se calculan una sola vez)
# ----------------------------------------------------------------------
N, K, D = 32, 6, 16
T = (D - 1) // 2

# Matriz generadora G (6 x 32). Fila 0: todos unos. Filas 1..5: el bit
# correspondiente de la posición j (0..31) escrito en binario.
G = np.array([
    [1] * 32,
    [0] * 16 + [1] * 16,
    ([0] * 8 + [1] * 8) * 2,
    ([0] * 4 + [1] * 4) * 4,
    ([0] * 2 + [1] * 2) * 8,
    [0, 1] * 16,
], dtype=np.uint8)

# Los 64 mensajes posibles de 6 bits. La fila i es i en binario (bit más
# significativo primero). Por eso, el índice i ES el valor del píxel (0..63).
MENSAJES = np.array([[(i >> (5 - j)) & 1 for j in range(6)] for i in range(64)], dtype=np.uint8)

# Diccionario: las 64 palabras válidas de 32 bits
DICC = (MENSAJES @ G) % 2

# Versión bipolar (0 -> -1, 1 -> +1) en float32, para decodificar por correlación
DICC_BIP = DICC.astype(np.float32) * 2 - 1

# Pesos para volver de 6 bits a un número: [32, 16, 8, 4, 2, 1]
PESOS = 2 ** np.arange(5, -1, -1)


# ----------------------------------------------------------------------
# Imagen <-> bits
# ----------------------------------------------------------------------
def cargar_imagen(ruta, max_lado=256):
    """Abre la imagen, la pasa a grises y la reduce (máx. max_lado píxeles)."""
    img = Image.open(ruta).convert("L")
    img.thumbnail((max_lado, max_lado))
    return np.array(img, dtype=np.uint8)


def cuantizar_6bits(matriz):
    """0..255 -> 0..63 (descarta los 2 bits menos significativos)."""
    return (matriz >> 2).astype(np.uint8)


def a_bloques(matriz6):
    """Matriz (alto, ancho) con valores 0..63 -> arreglo (N, 6) de bits."""
    bits8 = np.unpackbits(matriz6.reshape(-1, 1), axis=1)   # (N, 8)
    return bits8[:, 2:]                                      # nos quedamos con 6


def reconstruir(bloques, forma):
    """Arreglo (N, 6) de bits -> matriz con valores 0..63 y la forma original."""
    valores = bloques.astype(np.int32) @ PESOS
    return valores.reshape(forma).astype(np.uint8)


def a_visualizable(matriz6):
    """0..63 -> 0..255 para mostrar o comparar en la escala habitual."""
    return (matriz6.astype(np.int32) * 4).astype(np.uint8)


# ----------------------------------------------------------------------
# Codificador, canal y decodificador
# ----------------------------------------------------------------------
def codificar(bloques):
    """(N, 6) -> (N, 32): palabra de código = mensaje * G (mod 2)."""
    return (bloques @ G) % 2


def canal(palabras, p, rng):
    """Canal binario simétrico: cada bit se voltea con probabilidad p.
    Devuelve (palabras_recibidas, ruido)."""
    ruido = (rng.random(palabras.shape) < p).astype(np.uint8)
    return palabras ^ ruido, ruido


def decodificar(recibidas, tamano_lote=100_000):
    """Decodificación por máxima verosimilitud (mínima distancia de Hamming).

    Para cada palabra recibida se calcula la correlación con las 64 palabras
    válidas (en forma bipolar). La de mayor correlación es la de menor
    distancia de Hamming. Devuelve (N, 6) bits del mensaje estimado.
    """
    total = recibidas.shape[0]
    indices = np.empty(total, dtype=np.int64)
    for ini in range(0, total, tamano_lote):
        fin = min(ini + tamano_lote, total)
        lote = recibidas[ini:fin].astype(np.float32) * 2 - 1
        puntajes = lote @ DICC_BIP.T                 # (lote, 64)
        indices[ini:fin] = np.argmax(puntajes, axis=1)
    return MENSAJES[indices]


def transmitir_sin_codigo(bloques, p, rng):
    """Manda los 6 bits directamente por el canal. Devuelve (dañados, ruido)."""
    ruido = (rng.random(bloques.shape) < p).astype(np.uint8)
    return bloques ^ ruido, ruido


# ----------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------
def prob_teorica_fallo(p, n=N, t=T):
    """P(una palabra reciba más de t errores) = suma binomial de k=t+1 a n."""
    return sum(comb(n, k) * p**k * (1 - p)**(n - k) for k in range(t + 1, n + 1))


def _mse_psnr(a, b):
    mse = float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))
    psnr = float("inf") if mse == 0 else 10 * np.log10(255**2 / mse)
    return mse, psnr


def calcular_metricas(bloques_orig, bloques_sin, bloques_con, ruido, p, forma):
    """Devuelve un diccionario con las métricas de la simulación."""
    orig = a_visualizable(reconstruir(bloques_orig, forma))
    sin = a_visualizable(reconstruir(bloques_sin, forma))
    con = a_visualizable(reconstruir(bloques_con, forma))
    mse_sin, psnr_sin = _mse_psnr(orig, sin)
    mse_con, psnr_con = _mse_psnr(orig, con)

    errores_por_palabra = ruido.sum(axis=1)
    return {
        "p_canal": p,
        "p_medida": float(ruido.mean()),
        "ber_sin": float(np.mean(bloques_orig != bloques_sin)),
        "ber_con": float(np.mean(bloques_orig != bloques_con)),
        "mse_sin": mse_sin, "psnr_sin": psnr_sin,
        "mse_con": mse_con, "psnr_con": psnr_con,
        "palabras": int(ruido.shape[0]),
        "prom_errores_palabra": float(errores_por_palabra.mean()),
        "max_errores_palabra": int(errores_por_palabra.max()),
        "palabras_sobre_t": int(np.sum(errores_por_palabra > T)),
        "frac_sobre_t": float(np.mean(errores_por_palabra > T)),
        "frac_sobre_t_teorica": prob_teorica_fallo(p),
        "frac_palabras_mal": float(np.mean(np.any(bloques_orig != bloques_con, axis=1))),
    }


# ----------------------------------------------------------------------
# Un experimento completo (lo usará la interfaz)
# ----------------------------------------------------------------------
def simular(matriz_gris, p, semilla=None):
    """Corre todo el proceso sobre una imagen en grises (uint8) y devuelve
    (imagenes, metricas). Las imágenes están en escala 0..255 para mostrarlas."""
    rng = np.random.default_rng(semilla)
    m6 = cuantizar_6bits(matriz_gris)
    forma = m6.shape
    bloques = a_bloques(m6)

    # Ruta sin código
    bloques_sin, _ = transmitir_sin_codigo(bloques, p, rng)

    # Ruta con código
    palabras = codificar(bloques)
    recibidas, ruido = canal(palabras, p, rng)
    bloques_con = decodificar(recibidas)

    imagenes = {
        "original": a_visualizable(m6),
        "sin_codigo": a_visualizable(reconstruir(bloques_sin, forma)),
        "con_codigo": a_visualizable(reconstruir(bloques_con, forma)),
    }
    metricas = calcular_metricas(bloques, bloques_sin, bloques_con, ruido, p, forma)
    return imagenes, metricas
