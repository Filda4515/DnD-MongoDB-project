import sys
import httpx
from PyQt6.QtCore import Qt,QThread, pyqtSignal 
from PyQt6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QSplitter, QMainWindow, QListWidget, QLineEdit, QLabel, QFormLayout, QGroupBox, QGridLayout
from PyQt6.QtWidgets import QToolButton, QSizePolicy


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
        
        # Order of possible item stats
        self.item_stats_order = [
            "type", "cost", "weight", "damage", "damage_type", 
            "armor_class", "range", "properties", "desc"
        ]
        # Test Data
        
        self.all_data = {
            # --- Spells ---
            "Acid Arrow": {
                "category": "spell",  
                "Level": 2, "School": "Evocation", "Casting Time": "1 action",
                "Range": "90 feet", "Duration": "Instantaneous", 
                "Components": ["V", "S", "M"], "Concentration": False,
                "desc": "A shimmering green arrow streaks toward a target..."
            },
            "Detect Magic": {
                "category": "spell",
                "Level": 1, "School": "Divination", "Casting Time": "1 action",
                "Range": "Self", "Duration": "10 min", 
                "Components": ["V", "S"], "Concentration": True,
                "desc": "For the duration, you sense the presence of magic..."
            },
            # --- Monsters ---
            "Goblin Scout": {
                "category": "monster",
                "Armor Class": 15, "Hit Points": 7, "Speed": "30 ft.",
                "Strength": 8, "Dexterity": 14, "Constitution": 10, 
                "Intelligence": 10, "Wisdom": 8, "Charisma": 8,
                "inventory": ["Shortbow", "Potion of Healing"], 
                "desc": "Small and fast goblin."
            },
            "Orc Warrior": {
                "category": "monster",
                "Armor Class": 13, "Hit Points": 15, "Speed": "30 ft.",
                "Strength": 16, "Dexterity": 12, "Constitution": 16, 
                "Intelligence": 7, "Wisdom": 11, "Charisma": 10,
                "inventory": ["Iron Sword", "Heavy Crossbow"],
                "desc": "Brutal fighter."
            }        
            }
        
        
        # Splitter - for side screen and main screen 
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)
        
        # Left Panel
        self.left_widget = self.setup_left_panel()
        # Initial right panel 
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
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
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search Item")        
        self.search_bar.textChanged.connect(self.filter_items)
        # Test items for side screen
        self.list_widget = QListWidget()
        self.list_widget.addItems(self.all_data.keys())
        #self.list_widget.addItems(self.items_db.keys())
        self.list_widget.currentItemChanged.connect(self.display_items)
        # Adding Widgets to side screen
        layout.addWidget(self.search_bar)
        layout.addWidget(self.list_widget)
        return panel        
    
    # Filter items in search Bar
    def filter_items(self,text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())
    
    def clear_layout(self,layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
    
    def get_desc(self,data):
        desc_box = QVBoxLayout()
        
        return
           
    # Display the character info 
    def setup_character_layout(self, name, data):
        title = QLabel(f"{name}")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: darkred;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)
        
        # Combat stats
        combat_group = QGroupBox("Combat Stats")
        combat_layout = QFormLayout()
        for attr in ["Hit Points", "Armor Class", "Speed", "Challenge"]:
            item_attr = str(data.get(attr, "-"))
            combat_layout.addRow(QLabel(f"{attr}: "), QLabel(f"{item_attr}"))
        
        combat_group.setLayout(combat_layout)
        self.right_layout.addWidget(combat_group)
        
        # Attributes 
        abil_group = QGroupBox("Abbility Scores")
        grid =  QGridLayout()
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        
        row, col = 0,0
        for attr in abilities:
            vbox = QVBoxLayout
            lbl_name = QLabel(attr[:3].upper())
            lbl_name.setStyleSheet("color: gray; font-size: 10px;")
            lbl_val = QLabel(str(data.get(attr, "-")))
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
        
    # Display the spell info
    def setup_spell_layout(self, name, data):
        # Title
        title = QLabel(f"{name} (Spell)")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: blue;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)

        # Detail table
        group = QGroupBox("Spell Details")
        form = QFormLayout()
        
        attrs = ["Level", "School", "Casting Time", "Range", "Duration", "Components", "Concentration"]
        for attr in attrs:
            val = data.get(attr, "-")
            # Logic for coloring
            if isinstance(val, bool):
                lbl = QLabel("Yes" if val else "No")
                lbl.setStyleSheet("color: red; font-weight: bold;" if val else "")
            elif isinstance(val, list):
                lbl = QLabel(", ".join(val))
            else:
                lbl = QLabel(str(val))
            
            form.addRow(QLabel(f"{attr}:"), lbl)
        
        group.setLayout(form)
        self.right_layout.addWidget(group)

        # Description
        self.get_desc(data.get("desc", "")) 

    def setup_item_layout(self, name, data):
        title = QLabel(f"{name} (item)")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: green;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.right_layout.addWidget(title)
        group = QGroupBox("Item Details")
        form = QFormLayout()
        
        attrs = []
        for attr in attrs:
            val = data.get(attr, "-")
            lbl_name = QLabel(attr)
            lbl_value = QLabel(val)
            lbl_name.setStyleSheet("color: gray; font-size: 10px;")
            lbl_value.setStyleSheet("font-size: 16px; font-weight: bold;")
            form.addRow(lbl_name, lbl_value)
        group.setLayout(form)
        self.right_layout.addWidget(group)
        # TODO: Add description
        
        
    # Display currently selected item on right panel - main screen
    def display_items(self,current, previous):
        if not current:
            return
        name = current.text()
        data = self.all_data.get(name)
        
        if not data:
            return
        # Clear screen before loading new data
        self.clear_layout(self.right_layout)
        # Get category 
        item_category = data.get("category", "unknown")
        if item_category == "monster" or item_category == "character":
            self.setup_character_layout(name, data)
        elif item_category == "spell":
            self.setup_spell_layout(name, data)
        else: 
            self.right_layout.addWidget(QLabel("Couldn't load item"))        
        return

    def create_character(self):
        title = QLabel("Monster/CharacterCreation")
        
        group = QGroupBox("Creation")
        form = QFormLayout()
        return
    
    def create_item(self):
        return
    
    # TODO : Logic for function
    def set_image_from_url(self, url):
        return
    
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
