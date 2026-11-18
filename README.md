# Proyecto final · Teoría de Códigos

Aplicación interactiva que compara la transmisión de imágenes con Reed–Muller RM(1,5) y el Golay binario extendido [24,12,8]. Reed–Muller se asocia con Mariner 9 y Golay con Voyager; la aplicación usa ambos como modelos didácticos para la transmisión de imágenes.

## Integrantes

- Daniel Andrade Cabarcas
- SHAROL CASTRO CARO
- JUAN ENRIQUEZ ERAZO
- Daniela Roncallo Torres

## Organización

- `interfaz/`: aplicación por etapas y ejemplos de imagen.
- `golay/`: codificación, canal y decodificación Golay.
- `reed-muller/`: codificación, canal y decodificación Reed–Muller.

## Ejecución

La interfaz usa PyQt6. Desde la carpeta raíz instala las dependencias con `pip install -r requirements.txt` y ejecuta `python interfaz/app.py`.

La ventana se abre maximizada. Avanza con las flechas laterales o las teclas ← y →; cada paso tiene su propia diapositiva y una transición horizontal.

1. En la primera pantalla, elige una imagen y selecciona Golay o Reed–Muller. Se convierte a escala de grises y se reduce a un máximo de 256 × 256 píxeles.
2. En la pantalla de transmisión, define la probabilidad de error por bit (0–50 %) y pulsa **Transmitir**. La imagen se muestra sola para destacar el efecto del canal sin código.
3. Avanza a la pantalla de decodificación y pulsa **Decodificar** para ver sola la imagen recuperada.
4. La última pantalla presenta las tres imágenes juntas para compararlas.

Golay usa bloques de 12 bits codificados en 24. Su distancia mínima es `d = 8`, así que el radio de corrección garantizado es `t = floor((d - 1) / 2) = 3`: si se alteran hasta 3 bits, la palabra original sigue siendo la única palabra válida a esa distancia. Con más errores el decodificador puede elegir una palabra incorrecta. Reed–Muller RM(1,5) codifica 6 bits en 32, tiene distancia mínima 16 y corrige hasta 7 errores por palabra. La salida conserva respectivamente 8 y 6 bits de intensidad por píxel.

### Nota histórica

La guía del curso presenta Golay en el contexto de las imágenes de Voyager. La documentación técnica de telemetría consultada precisa que, durante los encuentros con Júpiter y Saturno, el Golay (24,12) protegía datos científicos no visuales y de ingeniería, mientras que las imágenes usaban el canal convolucional. Por eso, esta aplicación aplica Golay a píxeles como una simulación educativa y no reproduce toda la cadena histórica de Voyager.

## Presentación y resultados

En una simulación reproducible sobre `moon_1.jpg` (96 × 64, cinco repeticiones por p), Reed–Muller obtuvo menor BER decodificado que Golay en todos los niveles medidos. A `p = 20 %`, Golay superó el BER sin código, coherente con que ese nivel de ruido excede con frecuencia su capacidad correctora de 3 errores por palabra.

| p | BER Golay, sin → con código | BER Reed–Muller, sin → con código |
|---:|---:|---:|
| 1 % | 0.009953 → 0.000049 | 0.009798 → 0.000000 |
| 5 % | 0.050037 → 0.006873 | 0.049843 → 0.000000 |
| 10 % | 0.099849 → 0.054989 | 0.099593 → 0.000407 |
| 20 % | 0.199015 → 0.222591 | 0.199436 → 0.031923 |

El método, la tabla PSNR y las conclusiones completas están en [interfaz/RESULTADOS.md](interfaz/RESULTADOS.md). La presentación en PDF (máximo 8 diapositivas) se entrega junto con el aplicativo y este README, en una carpeta comprimida.

### Fuentes

- Guía del Proyecto Final de Teoría de Códigos, MAT 4215, Universidad del Norte, temas 5 y 8.
- Range Commanders Council, [IRIG 106-17, capítulo 7, apéndice A](https://www.irig106.org/docs/106-17/chapter7.pdf): define el Golay binario extendido como [24,12,8] e indica su capacidad de corrección de 3 bits.
- Michael Rice, [“A History of Channel Coding in Aeronautical Mobile Telemetry and Deep-Space Telemetry”](https://pmc.ncbi.nlm.nih.gov/articles/PMC11353454/), *Entropy* 26(8), 694 (2024): describe el uso de Golay y los esquemas de canal de Voyager.

## Herramientas y autoría

Se utilizó **OpenAI Codex** como apoyo para diseñar y elaborar la interfaz en PyQt6, organizar el flujo por pantallas y documentar el proyecto. Codex también ayudó a preparar el módulo de simulación Golay. El grupo debe revisar el código y todos sus integrantes deben poder explicar y modificar los módulos.
