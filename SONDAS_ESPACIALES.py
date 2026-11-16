"""
Interfaz gráfica. Se ejecuta con:  python interfaz.py
Paso 1: solo el esqueleto visual. Los botones todavía no hacen nada.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from nucleo import cargar_imagen, simular, cuantizar_6bits, a_visualizable
import os
from tkinter import filedialog, messagebox


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Transmisión de imágenes con Reed-Muller")
        self.geometry("1100x750")

        # Estado que compartirán los botones
        self.ruta = None
        self.matriz = None

        # La fila 1 (imágenes) es la que crece al agrandar la ventana
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._crear_controles()
        self._crear_zona_imagenes()
        self._crear_zona_metricas()

    # ---------- Zona 1: controles ----------
    def _crear_controles(self):
        marco = ctk.CTkFrame(self)
        marco.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.btn_cargar = ctk.CTkButton(marco, text="Cargar imagen", command=self.cargar)
        self.btn_cargar.pack(side="left", padx=10, pady=10)

        self.lbl_archivo = ctk.CTkLabel(marco, text="Ninguna imagen cargada")
        self.lbl_archivo.pack(side="left", padx=10)

        self.btn_transmitir = ctk.CTkButton(marco, text="Transmitir", command=self.transmitir)
        self.btn_transmitir.pack(side="right", padx=10)

        self.entrada_p = ctk.CTkEntry(marco, width=70)
        self.entrada_p.insert(0, "10")
        self.entrada_p.pack(side="right", padx=(0, 5))

        ctk.CTkLabel(marco, text="Probabilidad de error del canal (%):").pack(side="right", padx=5)

    def cargar(self):
        ruta = filedialog.askopenfilename(
            title="Elige una imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not ruta:
            return
        try:
            matriz = cargar_imagen(ruta)
        except Exception:
            messagebox.showerror("Error", "No se pudo abrir la imagen")
            return

        self.ruta = ruta
        self.matriz = matriz
        self.lbl_archivo.configure(text=os.path.basename(ruta))

        self._dibujar(self.ejes[0], a_visualizable(cuantizar_6bits(matriz)), "Original (6 bits)")
        self.canvas.draw()

    def _dibujar(self, eje, imagen, titulo):
        eje.clear()
        eje.imshow(imagen, cmap="gray", vmin=0, vmax=255)
        eje.set_title(titulo)
        eje.axis("off")


    def transmitir(self):
        # 1. Debe haber una imagen cargada
        if self.matriz is None:
            messagebox.showerror("Error", "Primero carga una imagen")
            return

        # 2. Leer y validar el porcentaje
        try:
            p = float(self.entrada_p.get().replace(",", ".")) / 100
        except ValueError:
            messagebox.showerror("Error", "El porcentaje debe ser un número")
            return
        if not (0 <= p <= 0.5):
            messagebox.showerror("Error", "El porcentaje debe estar entre 0 y 50")
            return

        # 3. Llamar al núcleo
        imagenes, met = simular(self.matriz, p)

        # 4. Dibujar las tres imágenes
        claves = ["original", "sin_codigo", "con_codigo"]
        titulos = ["Original (6 bits)", "Sin código", "Con Reed-Muller"]
        for eje, clave, titulo in zip(self.ejes, claves, titulos):
            self._dibujar(eje, imagenes[clave], titulo)
        self.canvas.draw()

        # 5. Escribir las métricas
        texto = (
            f"Probabilidad de error del canal: {met['p_canal']*100:.1f} %   "
            f"(medida: {met['p_medida']*100:.2f} %)\n"
            f"BER sin código: {met['ber_sin']:.5f}     BER con Reed-Muller: {met['ber_con']:.5f}\n"
            f"PSNR sin código: {met['psnr_sin']:.1f} dB     PSNR con Reed-Muller: {met['psnr_con']:.1f} dB\n"
            f"Errores por palabra: promedio {met['prom_errores_palabra']:.2f}, "
            f"máximo {met['max_errores_palabra']}\n"
            f"Palabras con más de 7 errores: {met['palabras_sobre_t']} de {met['palabras']} "
            f"({met['frac_sobre_t']*100:.2f} %; teoría {met['frac_sobre_t_teorica']*100:.2f} %)\n"
            f"Píxeles mal decodificados: {met['frac_palabras_mal']*100:.2f} %"
        )
        self.txt_metricas.configure(state="normal")
        self.txt_metricas.delete("1.0", "end")
        self.txt_metricas.insert("1.0", texto)
        self.txt_metricas.configure(state="disabled")

    # ---------- Zona 2: las tres imágenes ----------
    def _crear_zona_imagenes(self):
        marco = ctk.CTkFrame(self)
        marco.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        self.fig = Figure(figsize=(12, 4))
        self.ejes = self.fig.subplots(1, 3)
        titulos = ["Original (6 bits)", "Sin código", "Con Reed-Muller"]
        for eje, titulo in zip(self.ejes, titulos):
            eje.set_title(titulo)
            eje.axis("off")
            eje.text(0.5, 0.5, "Sin imagen", ha="center", va="center", transform=eje.transAxes)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=marco)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    # ---------- Zona 3: métricas ----------
    def _crear_zona_metricas(self):
        marco = ctk.CTkFrame(self)
        marco.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))

        self.txt_metricas = ctk.CTkTextbox(marco, height=190)
        self.txt_metricas.pack(fill="x", padx=10, pady=10)
        self.txt_metricas.insert("1.0", "Las métricas aparecerán aquí después de transmitir.")
        self.txt_metricas.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()
