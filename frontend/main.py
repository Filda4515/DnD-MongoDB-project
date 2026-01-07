import sys
import httpx
from PyQt6.QtCore import Qt,QThread, pyqtSignal 
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QSplitter, QMainWindow, QListWidget, QLineEdit, QLabel, QFormLayout, QGroupBox



class StatusWorker(QThread):
    result_signal = pyqtSignal(str)

    def run(self):
        try:
            response = httpx.get("http://127.0.0.1:8000/status", timeout=5.0)
            self.result_signal.emit(f"Success: {response.text}")
        except Exception as e:
            self.result_signal.emit(f"Connection Failed: {e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DnD Main Window")
        self.resize(800,600)
        
        # Splitter - for side screen and main screen 
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        # Left Right Panel
        self.left_widget = self.setup_left_panel()
        self.right_widget = self.setup_right_panel()
                   
        # Add panels to splitter   
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        
        # Base size for panels  
        self.splitter.setSizes([200,600])
    
    
    # TODO: Changed the hardcoded items to call request from database
    # Setup the left panel 
    def setup_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5,5,5,5)
        # Left Panel - search bar
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("Seach Item")        
        # Test items for side screen
        list_widget = QListWidget()
        list_widget.addItems(["Item1", "Item2", "Item3"])
        list_widget.currentItemChanged.connect(self.display_items)
        # Adding Widgets to side screen
        layout.addWidget(search_bar)
        layout.addWidget(list_widget)
        return panel        
    
    # TODO: Changed the hardcoded stats to call request from database
    # Setup the right panel
    def setup_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Main Screen - items 
        # TODO: Make it prettier and display Image
        
        self.content_label = QLabel("Select Item from side panel")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter) 
        
        layout.addWidget(self.content_label)        
        self.stats_group = QGroupBox("Stats")
        self.stats_group.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        image_label = QLabel()
        
        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.form_layout.setFormAlignment(Qt.AlignmentFlag.AlignCenter)
        self.form_layout.setHorizontalSpacing(20)
        
        stats = {
            "Strength": 16,
            "Dexterity": 14,
            "Constitution": 15,
            "Intelligence": 8,
            "Wisdom": 12,
            "Charisma": 10
        }
        # Display stats 
        for stat, value in stats.items():
            left_label_name = QLabel(f"{stat}")
            left_label_value = QLabel(f"{value}")
            self.form_layout.addRow(left_label_name, left_label_value)
        
        # Filips test na lokalku databazu ig
        self.btn = QPushButton("Ping Server", self)
        self.btn.clicked.connect(self.run_worker)
        layout.addWidget(self.btn)
        

        self.stats_group.setLayout(self.form_layout)
        layout.addWidget(self.stats_group)
        
        return panel
    # Filter items in search Bar
    def filter_items(self,text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())
    # Display currently selected item on right panel - main screen
    def display_items(self,current, previous):
        if current:
            # TODO Display the items we get from an API
            return

    def run_worker(self):
        print("Pinging...")

        self.worker = StatusWorker()

        self.worker.result_signal.connect(print)
        self.worker.start()

    # TODO : Logic for function
    def set_image_from_url(self, url):
        return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
