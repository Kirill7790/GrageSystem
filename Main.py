"""
Точка входу в додаток.
Виконує наступні дії:
    - 1. Створює екземпляр QApplication.
    - 2. Ініціалізує головне вікно додатка.
    - 3. Відображає головне вікно додатка.
    - 4. Запускає головний цикл обробки подій.
"""

import sys
from PyQt6.QtWidgets import QApplication
from InventoryApp import InventoryApp
import logging
from logger_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()

    exit_code = app.exec()

    if hasattr(window, "db") and window.db:
        window.db.disconnect()

    sys.exit(exit_code)
