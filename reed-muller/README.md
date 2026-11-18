# Reed–Muller · Mariner 9

Implementación de **RM(1,5) [32,6,16]**. Cada bloque contiene los seis bits más significativos de un píxel y se transmite como 32 bits; la distancia mínima 16 permite corregir hasta 7 errores.

`reed_muller.py` separa el flujo en cuatro operaciones: `preparar` cuantiza y empaqueta los píxeles, `transmitir` codifica y aplica el canal binario simétrico, `decodificar` busca la palabra válida más correlacionada y `reconstruir` devuelve la imagen de 6 bits.

La matriz generadora corresponde a las evaluaciones de funciones afines binarias en cinco variables. La búsqueda por correlación es equivalente a elegir la palabra válida de mínima distancia de Hamming.
