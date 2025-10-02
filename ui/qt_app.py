from pathlib import Path
from PyQt6 import QtWidgets, QtGui, QtCore
import threading
import cv2
import faulthandler
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers.tokenization_utils_base")

from services.image_service import process_image
from services.video_service import process_video
from domain.models import MetadataEntity

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

        # очередь печати: [(row, col, text, index)]
        self._print_queue = []

        # глобальный таймер для печати
        self._print_timer = QtCore.QTimer(self)
        self._print_timer.timeout.connect(self._process_print_queue)
        self._print_timer.start(20)  # скорость печати (20мс на букву)

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

        self.open_btn = QtWidgets.QPushButton("Выбрать папку")
        self.open_btn.setFixedWidth(150)
        self.open_btn.clicked.connect(self.open_folder)
        bottom_layout.addWidget(self.open_btn)

        self.start_btn = QtWidgets.QPushButton("Старт")
        self.start_btn.setFixedWidth(150)
        self.start_btn.clicked.connect(self.start_processing)
        bottom_layout.addWidget(self.start_btn)

        bottom_layout.addStretch()

        self.stock_combo = QtWidgets.QComboBox()
        self.stock_combo.addItems(["Все", "Shutterstock", "Adobe Stock", "Pond5", "Getty", "Alamy"])
        self.stock_combo.setFixedWidth(200)
        bottom_layout.addWidget(self.stock_combo)

        self.export_btn = QtWidgets.QPushButton("Экспорт")
        self.export_btn.setFixedWidth(150)
        bottom_layout.addWidget(self.export_btn)

        bottom_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    def open_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку с медиафайлами")
        if folder:
            allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".avi", ".mkv"}
            self.files = [
                f for f in Path(folder).iterdir()
                if f.suffix.lower() in allowed_ext and not f.name.startswith(".")
            ]
            self.populate_table()

    def populate_table(self):
        """Добавляем файлы в таблицу"""
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

            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                pixmap = QtGui.QPixmap(str(f))
                if not pixmap.isNull():
                    preview_label.setPixmap(
                        pixmap.scaled(120, 120,
                                      QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                      QtCore.Qt.TransformationMode.SmoothTransformation)
                    )
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

        steps_per_file = self.table.columnCount() - 1  # исключаем превью
        self.progress.setMaximum(len(self.files) * steps_per_file)

        self.status_label.setText("Начинаем обработку...")

        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()

    def process_files(self):
        for i, f in enumerate(self.files, start=1):
            try:
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    meta = process_image(f, callback=lambda field, value, row=i-1: self.partial_update(row, field, value))
                elif f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                    meta = process_video(f, callback=lambda field, value, row=i-1: self.partial_update(row, field, value))
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

    @QtCore.pyqtSlot(int, str, str)
    def update_table_cell(self, row: int, field: str, value: str):
        """Добавляем задачу на печатание текста"""
        col_map = {"title": 1, "description": 2, "keywords": 3,
                   "category": 4, "flags": 5, "captions": 6}
        if field not in col_map:
            return

        col = col_map[field]
        item = QtWidgets.QTableWidgetItem("")
        self.table.setItem(row, col, item)

        # добавляем задачу в очередь
        self._print_queue.append((row, col, value, 0))

    def _process_print_queue(self):
        """Глобальная печать: 1 буква за тик"""
        if not self._print_queue:
            return

        row, col, text, index = self._print_queue[0]
        item = self.table.item(row, col)
        if not item:
            item = QtWidgets.QTableWidgetItem("")
            self.table.setItem(row, col, item)

        if index < len(text):
            item.setText(text[:index + 1])
            self._print_queue[0] = (row, col, text, index + 1)
        else:
            # закончили печатать этот текст
            self._print_queue.pop(0)
            self.progress.setValue(self.progress.value() + 1)
            if self.progress.value() >= self.progress.maximum():
                self.status_label.setText("✅ Обработка завершена")

    def partial_update(self, row: int, field: str, value: str):
        QtCore.QMetaObject.invokeMethod(
            self, "update_table_cell", QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(int, row), QtCore.Q_ARG(str, field), QtCore.Q_ARG(str, value)
        )


def run():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = AttribApp()
    window.show()
    sys.exit(app.exec())
