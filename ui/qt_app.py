from pathlib import Path
from PyQt6 import QtWidgets, QtGui, QtCore
import threading

from services.image_service import process_image
from services.video_service import process_video
from domain.models import MetadataEntity


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
        layout.addWidget(self.table)

        # Прогресс бар + статус
        self.progress = QtWidgets.QProgressBar()
        self.status_label = QtWidgets.QLabel("Idle")
        layout.addWidget(self.progress)
        layout.addWidget(self.status_label)

        # Нижняя панель с кнопками
        button_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(button_layout)

        self.open_btn = QtWidgets.QPushButton("Выбрать папку")
        self.open_btn.clicked.connect(self.open_folder)
        button_layout.addWidget(self.open_btn)

        self.start_btn = QtWidgets.QPushButton("Старт")
        self.start_btn.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_btn)

    def open_folder(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите папку с медиафайлами")
        if folder:
            self.files = [f for f in Path(folder).iterdir() if not f.name.startswith(".")]
            self.populate_table()

    def populate_table(self):
        """Добавляем файлы в таблицу пустыми строками (только превью и имя)"""
        self.table.setRowCount(0)
        for f in self.files:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item = QtWidgets.QTableWidgetItem(f.name)
            if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                pixmap = QtGui.QPixmap(str(f))
                if not pixmap.isNull():
                    icon = QtGui.QIcon(pixmap.scaled(96, 96, QtCore.Qt.AspectRatioMode.KeepAspectRatio))
                    item.setIcon(icon)
            else:
                item.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileDialogDetailedView))
            self.table.setItem(row, 0, item)

    def start_processing(self):
        if not self.files:
            return
        self.progress.setValue(0)
        self.progress.setMaximum(len(self.files))
        self.status_label.setText("Начинаем обработку...")

        thread = threading.Thread(target=self.process_files)
        thread.start()

    def process_files(self):
        for i, f in enumerate(self.files, start=1):
            try:
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                    meta = process_image(f)
                elif f.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv"]:
                    meta = process_video(f)
                else:
                    continue
            except Exception as e:
                print(f"❌ Ошибка {f.name}: {e}")
                continue

            self.results.append(meta)

            # Обновляем UI
            QtCore.QMetaObject.invokeMethod(
                self, "update_table_row", QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(int, i - 1), QtCore.Q_ARG(str, f.name), QtCore.Q_ARG(object, meta)
            )

            self.progress.setValue(i)
            self.status_label.setText(f"Обрабатываю {i}/{len(self.files)}: {f.name}")

        self.status_label.setText("✅ Обработка завершена")

    @QtCore.pyqtSlot(int, str, object)
    def update_table_row(self, row: int, filename: str, meta: MetadataEntity):
        """Заполняем строку таблицы готовыми данными"""
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
