"""Compara BER y PSNR sin código y tras decodificar cada código.

Ejecutar desde la raíz del proyecto: python interfaz/experimentos.py
La semilla fija y la imagen reducida hacen reproducible el experimento.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "golay"))
sys.path.insert(0, str(ROOT / "reed-muller"))
import golay
import reed_muller

IMAGE_PATH = ROOT / "interfaz" / "imagenes" / "moon_1.jpg"
MAX_SIDE = 96
PROBABILITIES = (0.01, 0.05, 0.10, 0.20)
REPETITIONS = 5
BASE_SEED = 20261117


def _psnr(reference, received):
    mse = np.mean((reference.astype(np.float64) - received.astype(np.float64)) ** 2)
    return float("inf") if mse == 0 else 10 * np.log10(255**2 / mse)


def _uncoded_transmission(image, module, probability, rng):
    """Aplica el mismo canal directamente a los bits de cada píxel."""
    if module is golay:
        pixels = image.reshape(-1)
        bits = np.unpackbits(pixels[:, None], axis=1)
        reference = image
    else:
        pixels = image.reshape(-1).astype(np.uint8) >> 2
        bits = np.unpackbits(pixels[:, None], axis=1)[:, 2:]
        reference = ((image >> 2) * 4).astype(np.uint8)

    noisy_bits = bits ^ (rng.random(bits.shape) < probability)
    restored = np.packbits(noisy_bits.astype(np.uint8), axis=1).reshape(image.shape)
    bit_errors = np.count_nonzero(noisy_bits != bits)
    return reference, restored, bit_errors / bits.size


def _coded_transmission(image, module, probability, rng):
    """Codifica, transmite y decodifica; devuelve BER y reconstrucción."""
    shape, messages = module.preparar(image)
    received = module.transmitir(messages, probability, rng)
    decoded = module.decodificar(received)
    restored = module.reconstruir(decoded, shape)

    if module is golay:
        original_bits = np.unpackbits(image.reshape(-1, 1), axis=1)
        decoded_bits = decoded[:, :8]
    else:
        quantized = image.reshape(-1).astype(np.uint8) >> 2
        original_bits = np.unpackbits(quantized[:, None], axis=1)[:, 2:]
        decoded_bits = decoded
    ber = np.count_nonzero(original_bits != decoded_bits) / original_bits.size
    return restored, ber


def run():
    with Image.open(IMAGE_PATH) as source:
        gray = source.convert("L")
        gray.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
        image = np.asarray(gray, dtype=np.uint8)

    codes = (("Golay", golay), ("Reed–Muller", reed_muller))
    results = []
    for code_index, (name, module) in enumerate(codes):
        for probability_index, probability in enumerate(PROBABILITIES):
            measurements = []
            for repetition in range(REPETITIONS):
                seed = BASE_SEED + code_index * 10_000 + probability_index * 100 + repetition
                rng = np.random.default_rng(seed)
                reference, noisy, ber_uncoded = _uncoded_transmission(image, module, probability, rng)
                decoded_image, ber_coded = _coded_transmission(image, module, probability, rng)
                measurements.append((
                    ber_uncoded,
                    ber_coded,
                    _psnr(reference, noisy),
                    _psnr(reference, decoded_image),
                ))
            averages = np.mean(np.asarray(measurements), axis=0)
            results.append((name, probability, *averages))

    print(f"Imagen: {IMAGE_PATH.relative_to(ROOT)} | tamaño: {image.shape[1]}x{image.shape[0]} | repeticiones: {REPETITIONS}")
    print("Codigo | p | BER sin codigo | BER con codigo | PSNR sin codigo (dB) | PSNR con codigo (dB)")
    for row in results:
        name = "Reed-Muller" if row[0] == "Reed–Muller" else row[0]
        print(f"{name} | {row[1]:.0%} | {row[2]:.6f} | {row[3]:.6f} | {row[4]:.2f} | {row[5]:.2f}")


if __name__ == "__main__":
    run()
