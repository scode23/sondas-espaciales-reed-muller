# Transmisión de imágenes con Reed-Muller (sondas espaciales)

**Teoría de Códigos (MAT 4215) · Proyecto final · Tema 5: Sondas espaciales**

**Integrantes:** [Daniel Andrade Cabarcas], [Sharol Castro Caro], [Juan Enriquez Erazo], [Daniela Roncallo Torres]

## Descripción

Simulación de la transmisión de una imagen por un canal binario simétrico (cada bit se voltea con probabilidad *p*), con y sin el código **Reed-Muller RM(1,5)** que usó la sonda Mariner 9.

- Parámetros del código: **[n, k, d] = [32, 6, 16]**. Cada píxel de 6 bits (64 niveles de gris) se codifica en una palabra de 32 bits; tasa R = 6/32.
- Corrige hasta **t = ⌊(d−1)/2⌋ = 7** errores por palabra.
- Decodificación por mínima distancia de Hamming (máxima correlación con las 64 palabras válidas).

## Cómo ejecutarlo

Requiere Python 3.11 (versión con la que se probó).

1. Instalar las librerías: `pip install -r requirements.txt`
2. Interfaz gráfica: `python SONDAS_ESPACIALES.py`
   - **Cargar imagen** → escribir el porcentaje de error del canal (0 a 50) → **Transmitir**.
   - Se muestran la imagen original (6 bits), la recibida sin código y la recuperada con Reed-Muller, junto con las métricas.
3. Gráficas de error contra *p*: `python Experimentos.py` (usa `imagenes/moon_1.jpg` y guarda `grafica_ber.png`).

## Archivos

| Archivo | Contenido |
|---|---|
| `nucleo.py` | Núcleo: matriz generadora G, codificador, canal, decodificador y métricas |
| `Experimentos.py` | Barrido de *p* y gráficas de BER y capacidad de corrección |
| `SONDAS_ESPACIALES.py` | Interfaz gráfica (customtkinter) |
| `imagenes/` | Imágenes de prueba |

## Resultados principales

[COMPLETAR después de correr `Experimentos.py`]

| p | BER sin código | BER con Reed-Muller | PSNR sin / con (dB) |
|---|---|---|---|
| [ ] | [ ] | [ ] | [ ] |

**Conclusión:** [COMPLETAR]

## Declaración de herramientas

[REVISAR Y AJUSTAR para que describa lo que realmente hizo cada integrante.]

Se usó **Claude (Anthropic)** como apoyo para: (1) explicar los conceptos del tema (Reed-Muller, decodificación por mínima distancia, métricas BER y PSNR); (2) proponer la estructura del proyecto en tres archivos y una versión de referencia del núcleo (`nucleo.py`), de `Experimentos.py` y de la interfaz, que luego el grupo revisó, probó y adaptó; (3) ayudar a depurar errores de ejecución y a usar git y GitHub.

Todos los integrantes revisaron el código del núcleo y pueden explicarlo y modificarlo en vivo.

## Fuentes

- Guía del proyecto final, Teoría de Códigos (MAT 4215), Universidad del Norte.
- [COMPLETAR: libros, artículos y páginas consultadas.]
- Imágenes: [COMPLETAR: origen de `moon.jpg` y `moon_1.jpg`].