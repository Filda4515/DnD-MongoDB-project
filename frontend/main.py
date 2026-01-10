import sys
import httpx
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication, QPushButton, QVBoxLayout, QWidget, QSplitter, QMainWindow, QListWidget, QLineEdit, QLabel,
    QFormLayout, QGroupBox, QGridLayout
)
from PyQt6.QtWidgets import QHBoxLayout, QFrame, QSpinBox, QComboBox, QMessageBox


class DataWorker(QThread):
    result_signal = pyqtSignal(dict)
    data_received = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, endpoint, method="GET", data=None):
        super().__init__()
        self.endpoint = endpoint
        self.method = method
        self.data = data

    def run(self):
        try:
            url = f"http://127.0.0.1:8000/{self.endpoint}"

            with httpx.Client(timeout=5.0) as client:
                if self.method == "GET":
                    response = client.get(url)
                elif self.method == "POST":
                    response = client.post(url, json=self.data)
                elif self.method == "DELETE":
                    response = client.delete(url)
            response.raise_for_status()
            self.data_received.emit(response.json())
        except Exception as e:
            self.error_signal.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DnD Main Window")
        self.resize(800, 600)

        self.display_labels = {
            "name": "Name",
            "ac": "Armor Class",
            "hp": "Hit Points",
            "speed": "Speed",
            "challenge": "Challenge Rating",
            "strength": "STR",
            "dexterity": "DEX",
            "constitution": "CON",
            "intelligence": "INT",
            "wisdom": "WIS",
            "charisma": "CHA",
            "desc": "Description"
            }

        self.all_data = {}

        # Splitter - for side screen and main screen
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # Left Panel
        self.left_widget = self.setup_left_panel()
        # Initial right panel
        self.right_widget = QWidget()
        self.main_right_layout = QVBoxLayout(self.right_widget)
        self.main_right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Buttons for creation
        self.button_layout = QHBoxLayout()
        self.btn_char = QPushButton("New Character")
        self.btn_char.clicked.connect(self.create_monster)
        self.btn_item = QPushButton("New Item")
        self.btn_item.clicked.connect(self.create_item)

        self.button_layout.addWidget(self.btn_char)
        self.button_layout.addWidget(self.btn_item)

        self.main_right_layout.addLayout(self.button_layout)
        # Separation Line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_right_layout.addWidget(line)

        # Information Layout
        self.right_layout = QVBoxLayout()
        self.main_right_layout.addLayout(self.right_layout)

        # Add panels to splitter
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        # Base size for panels
        self.splitter.setSizes([200, 600])

        self.fetch_all_data()

    # Setup the left panel
    def setup_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Item")
        self.search_bar.textChanged.connect(self.filter_items)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self.all_data.keys())
        self.list_widget.currentItemChanged.connect(self.display_items)
        # Adding Widgets to side screen
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        return panel

    def fetch_all_data(self):
        # Fetch monsters
        self.monster_worker = DataWorker("monsters")
        self.monster_worker.data_received.connect(lambda data: self.on_data_loaded(data, "monster"))
        self.monster_worker.error_signal.connect(self.on_api_error)
        self.monster_worker.start()

        # Fetch items
        self.item_worker = DataWorker("items")
        self.item_worker.data_received.connect(lambda data: self.on_data_loaded(data, "item"))
        self.item_worker.error_signal.connect(self.on_api_error)
        self.item_worker.start()

    def on_data_loaded(self, data_list, category_type):
        for item in data_list:
            item["category"] = category_type
            name = item.get("name")
            self.all_data[name] = item

        # Refresh the list widget
        self.list_widget.clear()
        self.list_widget.addItems(self.all_data.keys())

    def on_api_error(self, message):
        QMessageBox.critical(self, "API Error", f"Request failed: {message}")

    # Display currently selected item on right panel - main screen
    def display_items(self, current):
        if not current:
            return
        name = current.text()
        data = self.all_data.get(name)

        if not data:
            return

        self.clear_layout(self.right_layout)

        item_category = data.get("category", "unknown")
        if item_category == "monster":
            self.setup_monster_layout(name, data)
        elif item_category == "item":
            self.setup_item_layout(name, data)
        else:
            self.right_layout.addWidget(QLabel("Couldn't load item"))
        return

    # Display the monster info
    def setup_monster_layout(self, name, data):
        title = QLabel(f"{name}")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: darkred;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)

        # Combat stats
        combat_group = QGroupBox("Combat Stats")
        combat_layout = QFormLayout()
        for key in ["hp", "ac", "speed", "challenge"]:
            val = str(data.get(key, "-"))

            display_name = self.display_labels.get(key, key.title())

            combat_layout.addRow(QLabel(f"{display_name}: "), QLabel(val))

        combat_group.setLayout(combat_layout)
        self.right_layout.addWidget(combat_group)

        # Attributes
        abil_group = QGroupBox("Abbility Scores")
        grid = QGridLayout()
        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

        row, col = 0, 0
        for key in abilities:
            lbl_name = QLabel(key[:3].upper())
            lbl_name.setStyleSheet("color: gray; font-size: 10px;")
            lbl_val = QLabel(str(data.get(key, "-")))
            lbl_val.setStyleSheet("font-size: 16px; font-weight: bold;")

            # Vloženie do gridu cez kontajner (aby to bolo pekne pod sebou)
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.addWidget(lbl_name, alignment=Qt.AlignmentFlag.AlignCenter)
            container_layout.addWidget(lbl_val, alignment=Qt.AlignmentFlag.AlignCenter)

            grid.addWidget(container, row, col)

            col += 1
            if col > 2:
                col = 0
                row += 1
        abil_group.setLayout(grid)
        self.right_layout.addWidget(abil_group)

        self.get_desc(data.get("desc", ""))

    # Display the item info
    def setup_item_layout(self, name, data):
        title = QLabel(f"{name} (Item)")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #E67E22;")  # Oranžová pre itemy
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)

        group = QGroupBox("Item Details")
        form = QFormLayout()

        attrs = ["weight", "value", "rarity"]

        for attr in attrs:
            raw_val = data.get(attr, "-")

            val_str = str(raw_val)

            lbl_name = QLabel(attr.title() + ":")
            lbl_value = QLabel(val_str)

            lbl_name.setStyleSheet("color: gray; font-size: 12px;")
            lbl_value.setStyleSheet("font-size: 16px; font-weight: bold;")

            form.addRow(lbl_name, lbl_value)

        group.setLayout(form)
        self.right_layout.addWidget(group)

        desc_text = data.get("desc", "")
        if desc_text:
            lbl_desc = QLabel("Description:")
            lbl_desc.setStyleSheet("font-weight: bold; margin-top: 10px;")
            self.right_layout.addWidget(lbl_desc)

            val_desc = QLabel(str(desc_text))
            val_desc.setWordWrap(True)
            val_desc.setStyleSheet("font-style: italic; color: #444;")
            self.right_layout.addWidget(val_desc)

    # Save created entity
    def save_data(self, endpoint, data_to_save):
        self.save_worker = DataWorker(endpoint, method="POST", data=data_to_save)

        # 2. Prepojíme signály
        self.save_worker.result_signal.connect(self.on_save_success)  # Úspech
        self.save_worker.error_signal.connect(self.on_api_error)

        # 3. Spustíme
        self.save_worker.start()

    def on_save_success(self, response_data):
        name = response_data.get("name")
        if not name:
            return

        # 1. Pridaj do lokálnych dát
        # Ak API nevratilo kategoriu, doplníme ju, aby fungovalo klikanie
        if "category" not in response_data:
            response_data["category"] = "monster"

        self.all_data[name] = response_data

        # 2. Pridaj položku do QListWidgetu
        self.list_widget.addItem(name)

    # Filter items in search Bar
    def filter_items(self, text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def get_desc(self, data):
        # desc_box = QVBoxLayout()  TODO:???

        return

    def create_monster(self):
        self.clear_layout(self.right_layout)

        # Title
        title = QLabel("Create New Character / Monster")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078D7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)

        # Dictionary Inicialization
        self.form_inputs = {}

        # Basic Info
        group_basic = QGroupBox("Basic Info")
        form_basic = QFormLayout()

        self.form_inputs["name"] = QLineEdit()
        form_basic.addRow("Name:", self.form_inputs["name"])

        self.form_inputs["desc"] = QLineEdit()
        form_basic.addRow("Description:", self.form_inputs["desc"])

        self.form_inputs["held_item_id"] = QComboBox()
        self.form_inputs["held_item_id"].addItem("None", None)
        for name, item_data in self.all_data.items():
            if item_data.get("category") == "item":
                self.form_inputs["held_item_id"].addItem(name, item_data.get("_id"))
        form_basic.addRow("Equipped Item:", self.form_inputs["held_item_id"])

        group_basic.setLayout(form_basic)
        self.right_layout.addWidget(group_basic)

        # Combat Stats
        group_combat = QGroupBox("Combat Stats")
        form_combat = QFormLayout()

        self.form_inputs["hp"] = QSpinBox()
        self.form_inputs["hp"].setRange(1, 1000)  # Rozsah 1 až 1000
        form_combat.addRow("Hit Points:", self.form_inputs["hp"])

        self.form_inputs["ac"] = QSpinBox()
        self.form_inputs["ac"].setRange(1, 50)
        self.form_inputs["ac"].setValue(10)  # Default hodnota
        form_combat.addRow("Armor Class:", self.form_inputs["ac"])

        self.form_inputs["speed"] = QLineEdit()
        self.form_inputs["speed"].setPlaceholderText("e.g. 30 ft.")
        form_combat.addRow("Speed:", self.form_inputs["speed"])

        self.form_inputs["challenge"] = QLineEdit()
        form_combat.addRow("Challenge Rating:", self.form_inputs["challenge"])

        group_combat.setLayout(form_combat)
        self.right_layout.addWidget(group_combat)

        # Ability Scores
        group_stats = QGroupBox("Ability Scores")
        grid_stats = QGridLayout()

        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

        row, col = 0, 0
        for attr in abilities:
            lbl = QLabel(attr[:3].upper())
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            spin = QSpinBox()
            spin.setRange(1, 30)
            spin.setValue(10)

            self.form_inputs[attr] = spin

            grid_stats.addWidget(lbl, row, col)
            grid_stats.addWidget(spin, row + 1, col)

            col += 1
            if col > 2:
                col = 0
                row += 2

        group_stats.setLayout(grid_stats)
        self.right_layout.addWidget(group_stats)

        # Save Button
        btn_save = QPushButton("Save Character")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        btn_save.clicked.connect(self.save_monster_data)
        self.right_layout.addWidget(btn_save)

    def save_monster_data(self):
        data = {}

        for key, widget in self.form_inputs.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
                data[key] = value
            elif isinstance(widget, QSpinBox):
                data[key] = widget.value()
            elif isinstance(widget, QComboBox):
                data[key] = widget.currentData()

        required_fields = ["name", "desc", "speed", "challenge"]
        missing_fields = []
        for field in required_fields:
            if not data.get(field):
                missing_fields.append(self.display_labels.get(field, field.capitalize()))

        if missing_fields:
            error_msg = "The following fields are required:\n\n" + "\n".join(missing_fields)
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        endpoint = "monsters"
        self.save_data(endpoint, data)

    def create_item(self):
        return

    # TODO : Logic for function
    def set_image_from_url(self, url):
        return


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
