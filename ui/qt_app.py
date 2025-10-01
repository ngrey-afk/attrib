from pathlib import Path
from PyQt6 import QtWidgets, QtGui, QtCore
import threading
import cv2
import faulthandler

from services.image_service import process_image
from services.video_service import process_video
from domain.models import MetadataEntity

# Включаем трассировку крашей (важно для Windows + PyTorch)
faulthandler.enable()


def get_video_preview(path: Path, size=(96, 96)):
    """Достаём первый кадр видео как превью"""
    cap = cv2.VideoCapture(str(path))
    success, frame = cap.read()
    cap.release()
    if success:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame.data, w, h, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        return pixmap.scaled(*size, QtCore.Qt.AspectRatioMode.KeepAspectRatio)
    else:
        return None


class AttribApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Metadata Tool (PyQt)")
        self.resize(1400, 900)

        self.results: list[MetadataEntity] = []
        self.files: list[Path] = []

        # Центральный виджет
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Таблица
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Preview", "Title", "Description", "Keywords",
            "Category", "Flags", "Captions"
        ])
        self.table.setIconSize(QtCore.QSize(96, 96))
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Автовысота строк
        self.table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setMinimumSectionSize(140)
        layout.addWidget(self.table)

        # Прогресс и статус
        self.progress = QtWidgets.QProgressBar()
        self.status_label = QtWidgets.QLabel("Готово к работе")
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        # Нижняя панель
        bottom_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(bottom_layout)

        # Левая часть: кнопки
        left_box = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(left_box, stretch=1)

        self.open_btn = QtWidgets.QPushButton("Выбрать папку")
        self.open_btn.setFixedWidth(150)
        self.open_btn.clicked.connect(self.open_folder)
        left_box.addWidget(self.open_btn)

        self.start_btn = QtWidgets.QPushButton("Старт")
        self.start_btn.setFixedWidth(150)
        self.start_btn.clicked.connect(self.start_processing)
        left_box.addWidget(self.start_btn)

        # Spacer
        bottom_layout.addStretch()

        # Правая часть: выбор стока + экспорт
        right_box = QtWidgets.QHBoxLayout()
        bottom_layout.addLayout(right_box, stretch=1)

        self.stock_combo = QtWidgets.QComboBox()
        self.stock_combo.addItems(["Все", "Shutterstock", "Adobe Stock", "Pond5", "Getty", "Alamy"])
        self.stock_combo.setFixedWidth(200)
        right_box.addWidget(self.stock_combo)

        self.export_btn = QtWidgets.QPushButton("Экспорт")
        self.export_btn.setFixedWidth(150)
        right_box.addWidget(self.export_btn)

        bottom_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)


    def open_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку с медиафайлами")
        if folder:
            self.files = [f for f in Path(folder).iterdir() if not f.name.startswith(".")]
            self.populate_table()


    def populate_table(self):
        """Добавляем файлы в таблицу: превью + имя файла снизу"""
        self.table.setRowCount(0)

        for f in self.files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            cell_widget = QtWidgets.QWidget()
            vbox = QtWidgets.QVBoxLayout(cell_widget)
            vbox.setContentsMargins(2, 2, 2, 2)
            vbox.setSpacing(2)

            preview_label = QtWidgets.QLabel()
            preview_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

            # ---- Картинки ----
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                pixmap = QtGui.QPixmap(str(f))
                if not pixmap.isNull():
                    preview_label.setPixmap(
                        pixmap.scaled(120, 120,
                                      QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                      QtCore.Qt.TransformationMode.SmoothTransformation)
                    )

            # ---- Видео (анимируем кадры через QTimer) ----
            elif f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                from services.video_service import extract_frames, get_video_duration

                try:
                    duration = get_video_duration(f)
                    num_frames = 3 if duration <= 10 else 5
                    frame_paths = extract_frames(f, num_frames)

                    frames = []
                    for frame_path in frame_paths:
                        pixmap = QtGui.QPixmap(str(frame_path))
                        if not pixmap.isNull():
                            frames.append(
                                pixmap.scaled(120, 120,
                                              QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                              QtCore.Qt.TransformationMode.SmoothTransformation)
                            )

                    if frames:
                        preview_label.setPixmap(frames[0])

                        def cycle_frames(label=preview_label, frames=frames):
                            current = getattr(label, "_frame_index", 0)
                            next_index = (current + 1) % len(frames)
                            label.setPixmap(frames[next_index])
                            label._frame_index = next_index

                        timer = QtCore.QTimer(preview_label)
                        timer.timeout.connect(cycle_frames)
                        timer.start(500)
                        preview_label._frame_index = 0
                        preview_label._timer = timer
                    else:
                        preview_label.setPixmap(
                            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay).pixmap(96, 96)
                        )

                except Exception as e:
                    print(f"⚠️ Ошибка при создании превью видео {f}: {e}")
                    preview_label.setPixmap(
                        self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay).pixmap(96, 96)
                    )

            # ---- Остальные файлы ----
            else:
                icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
                preview_label.setPixmap(icon.pixmap(96, 96))

            vbox.addWidget(preview_label)

            text_label = QtWidgets.QLabel(f.name)
            text_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            text_label.setWordWrap(True)
            text_label.setStyleSheet("font-size: 9pt;")
            vbox.addWidget(text_label)

            self.table.setCellWidget(row, 0, cell_widget)


    def start_processing(self):
        if not self.files:
            return
        self.progress.setValue(0)
        self.progress.setMaximum(len(self.files))
        self.status_label.setText("Начинаем обработку...")

        # 🔥 Один рабочий поток, без конкуренции PyTorch
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def process_files(self):
        for i, f in enumerate(self.files, start=1):
            try:
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    meta = process_image(f)
                elif f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                    print(f"▶️ Обрабатываю видео: {f}")
                    meta = process_video(f)
                else:
                    continue
            except Exception as e:
                print(f"❌ Ошибка {f.name}: {e}")
                continue

            self.results.append(meta)

            QtCore.QMetaObject.invokeMethod(
                self, "update_table_row", QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(int, i - 1), QtCore.Q_ARG(str, f.name), QtCore.Q_ARG(object, meta)
            )

            self.progress.setValue(i)
            self.status_label.setText(f"Обрабатываю {i}/{len(self.files)}: {f.name}")

        self.status_label.setText("✅ Обработка завершена")

    @QtCore.pyqtSlot(int, str, object)
    def update_table_row(self, row: int, filename: str, meta: MetadataEntity):
        self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(meta.title or ""))
        self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(meta.description or ""))
        self.table.setItem(row, 3, QtWidgets.QTableWidgetItem(", ".join(meta.keywords or [])))
        self.table.setItem(row, 4, QtWidgets.QTableWidgetItem(meta.category or ""))
        self.table.setItem(row, 5, QtWidgets.QTableWidgetItem(str(meta.flags or {})))
        self.table.setItem(row, 6, QtWidgets.QTableWidgetItem("\n".join(meta.captions or [])))


def run():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = AttribApp()
    window.show()
    sys.exit(app.exec())
