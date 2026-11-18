"""Interfaz espacial con diapositivas para comparar Golay y Reed–Muller."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtGui import QImage, QKeySequence, QPixmap, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "golay"))
sys.path.insert(0, str(ROOT / "reed-muller"))
import golay
import reed_muller


class ImageView(QFrame):
    """Panel que ajusta una imagen gris al espacio disponible."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setObjectName("imagePanel")
        self._pixmap = QPixmap()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        self.heading = QLabel(title)
        self.heading.setObjectName("imageHeading")
        self.heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview = QLabel("La imagen aparecerá aquí")
        self.preview.setObjectName("imagePreview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(200, 170)
        self.preview.setWordWrap(True)
        layout.addWidget(self.heading)
        layout.addWidget(self.preview, 1)

    def set_image(self, image):
        if image is None:
            self._pixmap = QPixmap()
            self.preview.setPixmap(QPixmap())
            self.preview.setText("La imagen aparecerá aquí")
            return
        gris = np.ascontiguousarray(image, dtype=np.uint8)
        alto, ancho = gris.shape
        qimage = QImage(gris.data, ancho, alto, ancho, QImage.Format.Format_Grayscale8).copy()
        self._pixmap = QPixmap.fromImage(qimage)
        self._ajustar()

    def _ajustar(self):
        if not self._pixmap.isNull():
            self.preview.setPixmap(self._pixmap.scaled(
                self.preview.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._ajustar()


class SlideDeck(QWidget):
    """Contenedor de páginas con transición horizontal animada."""

    page_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pages = []
        self.current = 0
        self.animating = False
        self.animation_group = None

    def add_page(self, page):
        page.setParent(self)
        page.hide()
        self.pages.append(page)
        if len(self.pages) == 1:
            page.setGeometry(self.rect())
            page.show()

    def go(self, index):
        if self.animating or not 0 <= index < len(self.pages) or index == self.current:
            return
        width = self.width()
        outgoing = self.pages[self.current]
        incoming = self.pages[index]
        direction = 1 if index > self.current else -1
        incoming.setGeometry(direction * width, 0, width, self.height())
        incoming.show()
        incoming.raise_()

        salida = QPropertyAnimation(outgoing, b"pos", self)
        salida.setDuration(380)
        salida.setStartValue(outgoing.pos())
        salida.setEndValue(QPoint(-direction * width, 0))
        salida.setEasingCurve(QEasingCurve.Type.InOutCubic)

        entrada = QPropertyAnimation(incoming, b"pos", self)
        entrada.setDuration(380)
        entrada.setStartValue(incoming.pos())
        entrada.setEndValue(QPoint(0, 0))
        entrada.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(salida)
        self.animation_group.addAnimation(entrada)
        self.animating = True

        def terminar():
            outgoing.hide()
            outgoing.move(0, 0)
            incoming.setGeometry(self.rect())
            self.current = index
            self.animating = False
            self.page_changed.emit(index)

        self.animation_group.finished.connect(terminar)
        self.animation_group.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.animating and self.pages:
            self.pages[self.current].setGeometry(self.rect())


class SpaceTransmission(QMainWindow):
    """Flujo en cuatro pantallas: imagen, ruido, decodificación y comparativa."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Deep Space Signal · Teoría de Códigos")
        self.resize(1280, 850)
        self.setMinimumSize(980, 680)
        self.setStyleSheet(STYLE)

        self.image = None
        self.no_code_image = None
        self.decoded_image = None
        self.received_words = None
        self.image_shape = None
        self.probability = 0.10
        self.code_name = "Reed–Muller · Mariner 9"
        self.rng = np.random.default_rng()

        self._build_window()
        self._build_pages()
        self._connect_shortcuts()
        self._update_navigation(0)

    def _build_window(self):
        root = QWidget()
        self.setCentralWidget(root)
        main = QVBoxLayout(root)
        main.setContentsMargins(24, 18, 24, 18)
        main.setSpacing(14)

        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title = QLabel("DEEP SPACE  /  ERROR-CORRECTION LAB")
        title.setObjectName("eyebrow")
        subtitle = QLabel("Imágenes a través del espacio")
        subtitle.setObjectName("appTitle")
        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header.addLayout(title_block, 1)
        self.step_label = QLabel("01  /  04")
        self.step_label.setObjectName("stepCounter")
        header.addWidget(self.step_label, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        main.addLayout(header)

        self.progress = QProgressBar()
        self.progress.setRange(0, 4)
        self.progress.setValue(1)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(5)
        main.addWidget(self.progress)

        navigation = QHBoxLayout()
        navigation.setSpacing(12)
        self.previous_button = QPushButton("‹")
        self.previous_button.setObjectName("arrowButton")
        self.previous_button.setAccessibleName("Paso anterior")
        self.previous_button.setFixedWidth(58)
        self.previous_button.clicked.connect(lambda: self.deck.go(self.deck.current - 1))
        navigation.addWidget(self.previous_button, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.deck = SlideDeck()
        self.deck.page_changed.connect(self._update_navigation)
        navigation.addWidget(self.deck, 1)

        self.next_button = QPushButton("›")
        self.next_button.setObjectName("arrowButton")
        self.next_button.setAccessibleName("Paso siguiente")
        self.next_button.setFixedWidth(58)
        self.next_button.clicked.connect(lambda: self.deck.go(self.deck.current + 1))
        navigation.addWidget(self.next_button, alignment=Qt.AlignmentFlag.AlignVCenter)
        main.addLayout(navigation, 1)

        footer = QHBoxLayout()
        self.status = QLabel("Elige una imagen para iniciar la transmisión.")
        self.status.setObjectName("statusText")
        footer.addWidget(self.status, 1)
        self.restart_button = QPushButton("Nuevo experimento")
        self.restart_button.setObjectName("secondaryButton")
        self.restart_button.clicked.connect(self._restart)
        footer.addWidget(self.restart_button)
        main.addLayout(footer)

    def _build_pages(self):
        self._build_image_page()
        self._build_transmit_page()
        self._build_decode_page()
        self._build_compare_page()

    def _new_page(self, step, title, subtitle):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(26, 22, 26, 22)
        layout.setSpacing(12)
        kicker = QLabel(step)
        kicker.setObjectName("pageKicker")
        heading = QLabel(title)
        heading.setObjectName("pageTitle")
        heading.setWordWrap(True)
        description = QLabel(subtitle)
        description.setObjectName("pageDescription")
        description.setWordWrap(True)
        layout.addWidget(kicker)
        layout.addWidget(heading)
        layout.addWidget(description)
        return page, layout

    def _build_image_page(self):
        page, layout = self._new_page(
            "01  /  PREPARAR SEÑAL",
            "Elige la imagen y el código",
            "La imagen se convierte a escala de grises y se ajusta para simular una transmisión espacial.",
        )
        controls = QHBoxLayout()
        self.load_button = QPushButton("＋  Cargar imagen")
        self.load_button.setObjectName("primaryButton")
        self.load_button.clicked.connect(self._load_image)
        self.file_label = QLabel("Sin imagen seleccionada")
        self.file_label.setObjectName("mutedText")
        self.code_picker = QComboBox()
        self.code_picker.addItems(["Reed–Muller · Mariner 9", "Golay · Voyager"])
        self.code_picker.currentTextChanged.connect(self._change_code)
        controls.addWidget(self.load_button)
        controls.addWidget(self.file_label, 1)
        controls.addWidget(QLabel("Código"))
        controls.addWidget(self.code_picker)
        layout.addLayout(controls)
        self.original_view = ImageView("Imagen original")
        layout.addWidget(self.original_view, 1)
        self.deck.add_page(page)

    def _build_transmit_page(self):
        page, layout = self._new_page(
            "02  /  CANAL RUIDOSO",
            "La señal cruza el espacio",
            "Ajusta la probabilidad de que cada bit se invierta. La imagen de esta pantalla representa la transmisión sin código.",
        )
        controls = QHBoxLayout()
        controls.addWidget(QLabel("Probabilidad de error p"))
        self.probability_input = QDoubleSpinBox()
        self.probability_input.setRange(0, 50)
        self.probability_input.setDecimals(1)
        self.probability_input.setSuffix(" %")
        self.probability_input.setValue(10)
        controls.addWidget(self.probability_input)
        self.transmit_button = QPushButton("Transmitir señal")
        self.transmit_button.setObjectName("primaryButton")
        self.transmit_button.clicked.connect(self._transmit)
        controls.addWidget(self.transmit_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.noisy_view = ImageView("Vista del canal sin código")
        layout.addWidget(self.noisy_view, 1)
        self.transmit_info = QLabel("La imagen ruidosa aparecerá al transmitir.")
        self.transmit_info.setObjectName("infoCard")
        layout.addWidget(self.transmit_info)
        self.deck.add_page(page)

    def _build_decode_page(self):
        page, layout = self._new_page(
            "03  /  RECUPERAR MENSAJE",
            "Decodifica la señal recibida",
            "El decodificador encuentra la palabra válida más cercana y reconstruye los píxeles protegidos por el código.",
        )
        controls = QHBoxLayout()
        self.decode_button = QPushButton("Decodificar señal")
        self.decode_button.setObjectName("primaryButton")
        self.decode_button.clicked.connect(self._decode)
        controls.addWidget(self.decode_button)
        controls.addStretch(1)
        layout.addLayout(controls)
        self.decoded_view = ImageView("Imagen recuperada")
        layout.addWidget(self.decoded_view, 1)
        self.decode_info = QLabel("La imagen recuperada aparecerá después de decodificar.")
        self.decode_info.setObjectName("infoCard")
        layout.addWidget(self.decode_info)
        self.deck.add_page(page)

    def _build_compare_page(self):
        page, layout = self._new_page(
            "04  /  COMPARACIÓN FINAL",
            "Misión completada: compara las imágenes",
            "Observa qué información perdió el canal y qué parte pudo recuperar el código corrector.",
        )
        images = QHBoxLayout()
        images.setSpacing(12)
        self.compare_original = ImageView("Original")
        self.compare_noisy = ImageView("Sin código · ruido")
        self.compare_decoded = ImageView("Recuperada · código")
        images.addWidget(self.compare_original, 1)
        images.addWidget(self.compare_noisy, 1)
        images.addWidget(self.compare_decoded, 1)
        layout.addLayout(images, 1)
        self.compare_info = QLabel("Completa los pasos para ver los resultados.")
        self.compare_info.setObjectName("infoCard")
        layout.addWidget(self.compare_info)
        self.deck.add_page(page)

    def _connect_shortcuts(self):
        self.left_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Left), self)
        self.left_shortcut.activated.connect(lambda: self.deck.go(self.deck.current - 1))
        self.right_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Right), self)
        self.right_shortcut.activated.connect(lambda: self.deck.go(self.deck.current + 1))

    def _module(self):
        return golay if self.code_name.startswith("Golay") else reed_muller

    def _reference_image(self):
        if self._module() is golay:
            return self.image
        return ((self.image >> 2) * 4).astype(np.uint8)

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Elige una imagen", "", "Imágenes (*.jpg *.jpeg *.png *.bmp *.tif)"
        )
        if not path:
            return
        try:
            with Image.open(path) as source:
                gray = source.convert("L")
                gray.thumbnail((256, 256), Image.Resampling.LANCZOS)
                self.image = np.asarray(gray, dtype=np.uint8)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo abrir la imagen", str(error))
            return
        self._clear_results()
        self.file_label.setText(Path(path).name)
        self.original_view.set_image(self._reference_image())
        self.status.setText("Imagen lista. Usa la flecha derecha o → para configurar la transmisión.")
        self._update_navigation(self.deck.current)

    def _change_code(self, text):
        self.code_name = text
        if self.image is not None:
            self.original_view.set_image(self._reference_image())
        self._clear_results()

    def _transmit(self):
        if self.image is None:
            return
        self.probability = self.probability_input.value() / 100
        module = self._module()
        self.image_shape, blocks = module.preparar(self.image)
        self.received_words = module.transmitir(blocks, self.probability, self.rng)

        # La vista ruidosa muestra el caso de referencia sin codificación.
        if module is golay:
            source_bits = np.unpackbits(self.image.reshape(-1, 1), axis=1)
        else:
            pixels6 = self.image.reshape(-1).astype(np.uint8) >> 2
            source_bits = np.unpackbits(pixels6[:, None], axis=1)[:, 2:]
        flipped = source_bits ^ (self.rng.random(source_bits.shape) < self.probability)
        self.no_code_image = np.packbits(flipped.astype(np.uint8), axis=1).reshape(self.image_shape)
        self.decoded_image = None
        self.noisy_view.set_image(self.no_code_image)
        self.transmit_info.setText(
            f"p = {self.probability:.1%} · Se transmitió la referencia sin redundancia. "
            f"La señal protegida con {module.N} bits por bloque está lista para decodificarse."
        )
        self.decoded_view.set_image(None)
        self.decode_info.setText(
            f"{self._code_title()} corrige hasta {module.T} errores por bloque. Pulsa Decodificar señal para recuperar la imagen."
        )
        self.status.setText("Transmisión completada. Avanza con → para decodificar.")
        self._refresh_comparison()
        self._update_navigation(self.deck.current)

    def _decode(self):
        if self.received_words is None:
            return
        module = self._module()
        decoded_blocks = module.decodificar(self.received_words)
        self.decoded_image = module.reconstruir(decoded_blocks, self.image_shape)
        reference = self._reference_image()
        errors = int(np.count_nonzero(self.decoded_image != reference))
        count = self.decoded_image.size
        self.decoded_view.set_image(self.decoded_image)
        self.decode_info.setText(
            f"{self._code_title()} · corrige hasta {module.T} errores por bloque. "
            f"Píxeles diferentes de la referencia: {errors}/{count} ({errors / count:.2%})."
        )
        self.status.setText("Decodificación completada. Avanza con → para comparar las tres imágenes.")
        self._refresh_comparison()
        self._update_navigation(self.deck.current)

    def _refresh_comparison(self):
        if self.image is None:
            return
        self.compare_original.set_image(self._reference_image())
        if self.no_code_image is not None:
            self.compare_noisy.set_image(self.no_code_image)
        if self.decoded_image is not None:
            self.compare_decoded.set_image(self.decoded_image)
            errors = int(np.count_nonzero(self.decoded_image != self._reference_image()))
            count = self.decoded_image.size
            self.compare_info.setText(
                f"{self._code_title()} · p = {self.probability:.1%} · "
                f"píxeles distintos después de decodificar: {errors}/{count} ({errors / count:.2%})."
            )

    def _clear_results(self):
        self.received_words = None
        self.no_code_image = None
        self.decoded_image = None
        if hasattr(self, "noisy_view"):
            self.noisy_view.set_image(None)
            self.decoded_view.set_image(None)
            self.transmit_info.setText("La imagen ruidosa aparecerá al transmitir.")
            self.decode_info.setText("La imagen recuperada aparecerá después de decodificar.")
            self.compare_noisy.set_image(None)
            self.compare_decoded.set_image(None)
            self.compare_info.setText("Completa los pasos para ver los resultados.")
            self._update_navigation(self.deck.current)

    def _restart(self):
        self._clear_results()
        self.deck.go(0)
        self.status.setText("Listo para iniciar un nuevo experimento.")

    def _code_title(self):
        return "Golay [24,12,8] · Voyager" if self._module() is golay else "Reed–Muller [32,6,16] · Mariner 9"

    def _update_navigation(self, index):
        titles = ("01  /  04", "02  /  04", "03  /  04", "04  /  04")
        self.step_label.setText(titles[index])
        self.progress.setValue(index + 1)
        self.previous_button.setEnabled(index > 0)
        can_advance = (
            (index == 0 and self.image is not None)
            or (index == 1 and self.received_words is not None)
            or (index == 2 and self.decoded_image is not None)
        )
        self.next_button.setEnabled(can_advance and index < 3)
        self.restart_button.setVisible(index == 3)

STYLE = """
QMainWindow, QWidget { background: #07111F; color: #E7F0FF; font-family: 'Segoe UI'; font-size: 14px; }
QFrame#imagePanel { background: #0C1B2E; border: 1px solid #203A57; border-radius: 16px; }
QLabel#eyebrow, QLabel#pageKicker { color: #73D7F2; font-size: 11px; font-weight: 700; letter-spacing: 2px; }
QLabel#appTitle { color: #F4F8FF; font-size: 25px; font-weight: 700; }
QLabel#stepCounter { color: #8A9DB8; font-size: 16px; font-weight: 700; }
QLabel#pageTitle { color: #F4F8FF; font-size: 28px; font-weight: 700; }
QLabel#pageDescription, QLabel#mutedText, QLabel#statusText { color: #A7B7CC; }
QLabel#imageHeading { color: #A9BED8; font-size: 13px; font-weight: 600; }
QLabel#imagePreview { background: #07111F; color: #627994; border-radius: 10px; }
QLabel#infoCard { background: #10243A; color: #B8C9DE; padding: 12px 16px; border-radius: 10px; }
QProgressBar { background: #172A40; border: 0; border-radius: 2px; }
QProgressBar::chunk { background: #45C9E8; border-radius: 2px; }
QPushButton, QComboBox, QDoubleSpinBox { background: #142A43; color: #E7F0FF; border: 1px solid #2C4A6A; border-radius: 9px; padding: 10px 14px; }
QPushButton:hover { background: #1B395A; border-color: #45C9E8; }
QPushButton:disabled { color: #61748C; background: #101C2B; border-color: #1B2A3C; }
QPushButton#primaryButton { background: #176D8A; border-color: #35B9D6; color: white; font-weight: 700; }
QPushButton#primaryButton:hover { background: #2088A7; }
QPushButton#secondaryButton { background: transparent; }
QPushButton#arrowButton { font-size: 36px; font-weight: 300; padding: 3px; min-height: 72px; }
QComboBox QAbstractItemView { background: #10243A; color: #E7F0FF; selection-background-color: #176D8A; }
QDoubleSpinBox { min-width: 100px; }
"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = SpaceTransmission()
    window.showMaximized()
    sys.exit(app.exec())
