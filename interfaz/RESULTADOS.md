# Resultados de la simulación

## Método

Se usó `interfaz/imagenes/moon_1.jpg`, convertida a gris y reducida a **96 × 64 píxeles**. Se probaron probabilidades de inversión de bit `p = 1 %, 5 %, 10 % y 20 %`, con **5 repeticiones por código y valor de p**. La semilla base es `20261117`; el experimento se puede repetir desde la raíz con `python interfaz/experimentos.py`.

BER sin código se mide directamente sobre los bits del píxel. BER con código se mide sobre los bits de información recuperados, excluyendo los bits de relleno de Golay. PSNR compara cada imagen recibida con su referencia cuantizada; infinito significa que en las cinco repeticiones no hubo diferencias de intensidad en la imagen reconstruida.

## BER promedio

| p | Golay sin código | Golay decodificado | Reed–Muller sin código | Reed–Muller decodificado |
|---:|---:|---:|---:|---:|
| 1 % | 0.009953 | 0.000049 | 0.009798 | 0.000000 |
| 5 % | 0.050037 | 0.006873 | 0.049843 | 0.000000 |
| 10 % | 0.099849 | 0.054989 | 0.099593 | 0.000407 |
| 20 % | 0.199015 | 0.222591 | 0.199436 | 0.031923 |

## PSNR promedio (dB)

| p | Golay sin código | Golay decodificado | Reed–Muller sin código | Reed–Muller decodificado |
|---:|---:|---:|---:|---:|
| 1 % | 24.93 | ∞ | 24.68 | ∞ |
| 5 % | 17.65 | 28.24 | 17.74 | ∞ |
| 10 % | 14.68 | 18.38 | 14.57 | 39.91 |
| 20 % | 11.45 | 11.95 | 11.43 | 20.41 |

## Conclusión

En estas pruebas, ambos códigos redujeron el error para `p` de 1 % a 10 %, y Reed–Muller tuvo el BER decodificado menor en todos los niveles probados. A `p = 20 %`, Golay quedó por encima del BER sin código: con tanto ruido, el decodificador puede escoger una palabra incorrecta al exceder su radio garantizado de 3 errores por bloque. Reed–Muller aún redujo el BER, aunque no lo eliminó.

Los resultados son promedios de una imagen y cinco repeticiones; ilustran esta simulación y no garantizan el mismo rendimiento para otras imágenes, tamaños o secuencias de ruido. Los valores `∞` significan error cero observado en esta muestra, no corrección perfecta para cualquier transmisión.
