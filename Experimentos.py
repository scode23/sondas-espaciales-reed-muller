"""
Experimentos: barrido de la probabilidad de error p y gráficas para la ponencia.
Se ejecuta con:  python experimentos.py
"""
import numpy as np
import matplotlib.pyplot as plt
from nucleo import cargar_imagen, simular, prob_teorica_fallo


def barrido(matriz_gris, lista_p, repeticiones=5):
    """Corre simular() para cada p, con varias semillas, y promedia las métricas."""
    claves = ["ber_sin", "ber_con", "frac_sobre_t", "frac_palabras_mal"]
    res = {k: [] for k in claves}
    res["p"] = list(lista_p)
    res["teorica"] = [prob_teorica_fallo(p) for p in lista_p]

    for p in lista_p:
        mets = [simular(matriz_gris, p, semilla=s)[1] for s in range(repeticiones)]
        for k in claves:
            res[k].append(np.mean([m[k] for m in mets]))

    return {k: np.array(v) for k, v in res.items()}


def graficar(r, guardar=None):
    """Dibuja las dos gráficas. Si 'guardar' trae un nombre, guarda también un PNG."""
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))

    # Gráfica 1: BER contra p
    ber_con = np.where(r["ber_con"] > 0, r["ber_con"], np.nan)   # el 0 no existe en escala log
    ax[0].semilogy(r["p"], r["ber_sin"], "o-", label="Sin código")
    ax[0].semilogy(r["p"], ber_con, "s-", label="Con Reed-Muller")
    ax[0].set_xlabel("Probabilidad de error del canal (p)")
    ax[0].set_ylabel("BER (tasa de error de bits)")
    ax[0].set_title("Error antes y después del código")
    ax[0].grid(True, which="both", alpha=0.3)
    ax[0].legend()

    # Gráfica 2: palabras con más de 7 errores, medido vs teoría
    ax[1].plot(r["p"], r["teorica"], "k--", label="Teoría: P(>7 errores)")
    ax[1].plot(r["p"], r["frac_sobre_t"], "o", label="Medido: palabras con >7 errores")
    ax[1].plot(r["p"], r["frac_palabras_mal"], "s-", label="Medido: palabras mal decodificadas")
    ax[1].set_xlabel("Probabilidad de error del canal (p)")
    ax[1].set_ylabel("Fracción de palabras")
    ax[1].set_title("Capacidad de corrección (t = 7)")
    ax[1].grid(True, alpha=0.3)
    ax[1].legend()

    plt.tight_layout()
    if guardar:
        fig.savefig(guardar, dpi=150)
    plt.show()


if __name__ == "__main__":
    p_lista = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]
    img = cargar_imagen("imagenes/moon_1.jpg", max_lado=128)   # más chica = más rápido
    r = barrido(img, p_lista, repeticiones=5)
    graficar(r, guardar="grafica_ber.png")
