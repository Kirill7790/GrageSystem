import sys
from PyQt6.QtWidgets import QApplication
from InventoryApp import InventoryApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec())