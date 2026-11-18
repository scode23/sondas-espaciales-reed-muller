# Golay · Voyager

Implementación del Golay binario extendido **[24,12,8]**. Cada bloque contiene 12 bits de información y se transmite como 24 bits. La distancia mínima es `d = 8`, por lo que el radio de corrección garantizado es `t = floor((d - 1) / 2) = 3`. Con 4 o más errores, el decodificador de distancia mínima puede escoger otra palabra válida.

`golay.py` separa el flujo en cuatro operaciones: `preparar` empaqueta los píxeles, `transmitir` codifica y aplica el canal binario simétrico, `decodificar` busca la palabra válida más correlacionada y `reconstruir` vuelve a formar la imagen.

Para simplificar la demostración, cada píxel gris de 8 bits ocupa un bloque de 12 bits; sus cuatro bits finales son cero. La interfaz muestra la referencia sin código y la imagen recuperada con Golay.

Fuente de los parámetros y la capacidad correctora: [IRIG 106-17, capítulo 7, apéndice A](https://www.irig106.org/docs/106-17/chapter7.pdf).
