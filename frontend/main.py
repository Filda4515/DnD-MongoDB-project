import sys
import httpx
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget


class StatusWorker(QThread):
    result_signal = pyqtSignal(str)

    def run(self):
        try:
            response = httpx.get("http://127.0.0.1:8000/status", timeout=5.0)
            self.result_signal.emit(f"Success: {response.text}")
        except Exception as e:
            self.result_signal.emit(f"Connection Failed: {e}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.btn = QPushButton("Ping Server", self)
        self.btn.clicked.connect(self.run_worker)

        layout = QVBoxLayout(self)
        layout.addWidget(self.btn)

    def run_worker(self):
        print("Pinging...")

        self.worker = StatusWorker()

        self.worker.result_signal.connect(print)
        self.worker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
