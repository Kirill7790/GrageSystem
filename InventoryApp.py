import sys
import logging
import traceback

import pandas as pd
from PyQt6.QtGui import QColor, QAction
from PyQt6.QtCore import Qt, QDate, QTimer
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox, QTabWidget,
    QStatusBar, QMessageBox, QHeaderView, QDialog
)

from DBConnection import DBConnection
from InventoryItemForm import InventoryItemForm
from RentalForm import RentalForm
from ReturnForm import ReturnForm
from StatsWindow import StatsWindow

logger = logging.getLogger(__name__)

class InventoryApp(QMainWindow):
    """
    Головний клас додатку. В собі має головний інтерфейс користувача з чотирма вкладками.
    """
    def __init__(self):
        """
        Метод для ініціалізації головного вікна застосунку.
        Встановлює підключення до бази даних, створює UI.
        """
        super().__init__()
        self.setWindowTitle("Система обліку туристичного інвентарю")
        self.setGeometry(100, 100, 1200, 800)
        logger.info("Ініціалізація головного вікна додатку")

        # Підключення до бази даних
        logger.debug("Спроба підключення до бази даних")
        self.db = DBConnection()
        if not self.db.connect():
            logger.error("Не вдалося підключитися до бази даних")
            QMessageBox.critical(self, "Помилка", "Не вдалося підключитися до бази даних")
            sys.exit(1)
        logger.info("Підключення до бази даних успішне")

        # Головний віджет
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        # Основний layout
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)

        # Ініціалізація UI
        logger.debug("Ініціалізація UI")
        self.init_ui()

        # Завантаження початкових даних
        logger.debug("Завантаження початкових даних")
        self.load_initial_data()

        # Застосування стилів
        self.apply_styles()

        logger.info("Головне вікно успішно ініціалізовано")

    def init_ui(self):
        """
        Метод, що ініціалізує UI. Створює вкладки, та статус бар.
        """
        logger.info("Створення вкладок інтерфейсу")

        # Створення вкладок
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)


        # Вкладка інвентарю
        self.inventory_tab = QWidget()
        self.inventory_tab.setAccessibleName("Вкладка інвентарю")
        self.tabs.addTab(self.inventory_tab, "Інвентар")
        logger.debug("Вкладку 'Інвентар' створено")

        self.init_inventory_tab()

        # Вкладка історії використання
        self.history_tab = QWidget()
        self.history_tab.setAccessibleName("Вкладка історії використання")
        self.tabs.addTab(self.history_tab, "Історія використання")
        self.init_history_tab()
        logger.debug("Вкладку 'Історія використання' створено")

        # Вкладка оренди
        self.rental_tab = QWidget()
        self.rental_tab.setAccessibleName("Вкладка оренди")
        self.tabs.addTab(self.rental_tab, "Оренда")
        self.init_rental_tab()
        logger.debug("Вкладку 'Оренда' створено")

        # Вкладка статистики
        self.stats_tab = StatsWindow(self.db)
        self.stats_tab.setAccessibleName("Вкладка статистики")
        self.tabs.addTab(self.stats_tab, "Статистика")
        logger.debug("Вкладку 'Статистика' створено")

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово до роботи")
        logger.debug("Статус бар створено")

    def init_inventory_tab(self):
        """
        Метод для ініціалізації вкладки інвентарю. Створює панелі пошуку та фільтрів,
        таблицю з інвентарем та кнопки для керування.
        """
        logger.info("Ініціалізація вкладки 'Інвентар'")
        layout = QVBoxLayout()
        self.inventory_tab.setLayout(layout)

        # Панель пошуку
        search_panel = QWidget()
        search_layout = QHBoxLayout()
        search_panel.setLayout(search_layout)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за назвою або номером...")
        self.search_input.setAccessibleName("Поле пошуку інвентарю")
        self.search_input.setAccessibleDescription(
            "Введіть текст для пошуку предметів за назвою або інвентарним номером")
        self.search_input.textChanged.connect(self.filter_inventory)
        search_layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.setAccessibleName("Фільтр категорій")
        self.category_filter.setAccessibleDescription("Виберіть категорію для фільтрації інвентарю")
        self.category_filter.addItem("Всі категорії", None)
        search_layout.addWidget(self.category_filter)

        self.status_filter = QComboBox()
        self.status_filter.setAccessibleName("Фільтр статусів")
        self.status_filter.setAccessibleDescription("Виберіть статус доступності для фільтрації інвентарю")
        self.status_filter.addItem("Всі статуси", None)
        search_layout.addWidget(self.status_filter)

        layout.addWidget(search_panel)
        logger.debug("Панель пошуку предметів створено")

        # Таблиця інвентарю
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(8)
        self.inventory_table.setHorizontalHeaderLabels([
            "ID", "Номер", "Назва", "Категорія", "Статус", "Стан", "Цілісність (%)", "Примітки"
        ])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inventory_table.doubleClicked.connect(self.edit_inventory_item)
        layout.addWidget(self.inventory_table)
        logger.debug("Таблицю інвентарю створено")

        # Панель кнопок
        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        self.add_button = QPushButton("Додати")
        self.add_button.clicked.connect(self.add_inventory_item)
        button_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Редагувати")
        self.edit_button.clicked.connect(self.edit_inventory_item)
        button_layout.addWidget(self.edit_button)

        self.delete_button = QPushButton("Видалити")
        self.delete_button.clicked.connect(self.delete_inventory_item)
        button_layout.addWidget(self.delete_button)

        self.rent_button = QPushButton("Орендувати")
        self.rent_button.clicked.connect(self.rent_item)
        button_layout.addWidget(self.rent_button)

        self.refresh_button = QPushButton("Оновити")
        self.refresh_button.clicked.connect(self.load_inventory_data)
        button_layout.addWidget(self.refresh_button)

        layout.addWidget(button_panel)
        logger.debug("Панель кнопок створено")

    def init_history_tab(self):
        """
        Метод для ініціалізації вкладки історії використання інвентарю.
        Створює панелі пошуку та фільтрів, таблицю з данини використання предметів та кнопки для керування.
        """
        logger.info("Ініціалізація вкладки 'Історія використання'")
        layout = QVBoxLayout()
        self.history_tab.setLayout(layout)

        # Панель пошуку та фільтрів
        search_panel = QWidget()
        search_layout = QHBoxLayout()
        search_panel.setLayout(search_layout)

        # Поле пошуку
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Пошук за користувачем або предметом...")
        self.history_search.textChanged.connect(self.filter_history)
        search_layout.addWidget(self.history_search)

        # Комбобокс для сортування
        self.history_sort_combo = QComboBox()
        self.history_sort_combo.addItem("Сортування", None)
        self.history_sort_combo.addItem("Дата початку (за зростанням)", "start_date_asc")
        self.history_sort_combo.addItem("Дата початку (за спаданням)", "start_date_desc")
        self.history_sort_combo.addItem("Дата кінцю (за зростанням)", "end_date_asc")
        self.history_sort_combo.addItem("Дата кінцю (за спаданням)", "end_date_desc")
        self.history_sort_combo.addItem("Назва (А → Я)", "name_asc")
        self.history_sort_combo.addItem("Назва (Я → А)", "name_desc")
        self.history_sort_combo.addItem("Користувач (А → Я)", "user_asc")
        self.history_sort_combo.addItem("Користувач (Я → А)", "user_desc")
        self.history_sort_combo.currentIndexChanged.connect(self.load_history_data)
        search_layout.addWidget(self.history_sort_combo)

        layout.addWidget(search_panel)
        logger.debug("Панель пошуку історії використання створено")

        # Таблиця історії
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(9)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Номер предмету", "Предмет", "Користувач",
            "Початок", "Кінець", "Повернено", "Статус", "Примітки"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.history_table)
        logger.debug("Таблицю історії створено")

        # Панель кнопок
        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        # Кнопка оновлення
        self.history_refresh = QPushButton("Оновити")
        self.history_refresh.clicked.connect(self.load_history_data)
        button_layout.addWidget(self.history_refresh)

        # Кнопка очищення історії
        self.clear_history_button = QPushButton("Очистити історію")
        self.clear_history_button.clicked.connect(self.clear_history)
        button_layout.addWidget(self.clear_history_button)

        layout.addWidget(button_panel)
        logger.debug("Панель кнопок створено")



    def init_rental_tab(self):
        """
        Метод для ініціалізації вкладки активних оренд. Створює панелі пошуку та фільтрів,
        таблицю з даними про активні оренди та кнопками оновлення та повернення.
        """
        logger.info("Ініціалізація вкладки 'Оренда'")
        layout = QVBoxLayout()
        self.rental_tab.setLayout(layout)

        # Панель пошуку
        search_panel = QWidget()
        search_layout = QHBoxLayout()
        search_panel.setLayout(search_layout)

        self.rental_search = QLineEdit()
        self.rental_search.setPlaceholderText("Пошук за користувачем або предметом...")
        self.rental_search.textChanged.connect(self.filter_rentals)
        search_layout.addWidget(self.rental_search)

        self.rental_status_filter = QComboBox()
        self.rental_status_filter.addItem("Всі статуси", None)
        self.rental_status_filter.addItem("В оренді", "active")
        self.rental_status_filter.addItem("Повернені", "returned")
        self.rental_status_filter.addItem("Протерміновані", "overdue")
        search_layout.addWidget(self.rental_status_filter)

        layout.addWidget(search_panel)
        logger.debug("Панель пошуку оренд створено")

        # Таблиця оренди
        self.rental_table = QTableWidget()
        self.rental_table.setColumnCount(9)
        self.rental_table.setHorizontalHeaderLabels([
            "ID", "Номер предмету", "Предмет", "Орендар",
            "Початок", "Кінець", "Повернено", "Статус", "Примітки"
        ])
        self.rental_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rental_table.doubleClicked.connect(self.return_item)
        layout.addWidget(self.rental_table)
        logger.debug("Таблицю оренд створено")

        # Панель кнопок
        button_panel = QWidget()
        button_layout = QHBoxLayout()
        button_panel.setLayout(button_layout)

        self.return_button = QPushButton("Повернути")
        self.return_button.clicked.connect(self.return_item)
        button_layout.addWidget(self.return_button)

        self.refresh_rental_button = QPushButton("Оновити")
        self.refresh_rental_button.clicked.connect(self.load_rental_data)
        button_layout.addWidget(self.refresh_rental_button)

        layout.addWidget(button_panel)
        logger.debug("Панель кнопок створено")

    def load_initial_data(self):
        """
        Метод для завантаження початкових даних для всіх вкладок.
        """
        logger.info("Завантаження початкових даних")

        # Завантаження даних для фільтрів
        self.load_filter_data()

        # Завантаження даних інвентарю
        self.load_inventory_data()

        # Завантаження історії використання
        self.load_history_data()

        # Завантаження даних оренди
        self.load_rental_data()

        logger.info("Всі початкові дані завантажено")


    def load_filter_data(self):
        """
        Метод для завантаження даних для фільтрів категорій та статусів.
        """
        logger.info("Завантаження даних для фільтрів")
        try:
            # Завантаження категорій
            categories = self.db.get_categories()
            self.category_filter.clear()
            self.category_filter.addItem("Всі категорії", None)
            for _, row in categories.iterrows():
                self.category_filter.addItem(row['category_name'], row['category_id'])
            logger.debug(f"Завантажено {len(categories)} категорій")

            # Завантаження статусів
            statuses = self.db.get_statuses()
            self.status_filter.clear()
            self.status_filter.addItem("Всі статуси", None)
            for _, row in statuses.iterrows():
                self.status_filter.addItem(row['status_name'], row['status_id'])
            logger.debug(f"Завантажено {len(statuses)} статусів")

        except Exception as e:
            logger.error(f"Помилка завантаження даних фільтрів: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані фільтрів: {str(e)}")

    def load_inventory_data(self):
        """
        Метод для завантаження та відображення даних про інвентар у таблиці.
        Якщо цілісність предмета менше, ніж 20%, він підсвітиться світло-червоним кольором.
        """
        logger.info("Завантаження даних інвентарю")
        try:
            inventory_data = self.db.get_inventory_details()
            logger.debug(f"Отримано {len(inventory_data)} записів інвентарю")

            self.inventory_table.setRowCount(len(inventory_data))
            critical_count = 0

            for row_idx, row in inventory_data.iterrows():
                for col_idx, col in enumerate([
                    "ID предмету", "Предметний номер", "Назва предмету",
                    "Категорія", "Статус доступності", "Стан предмету",
                    "Цілісність (%)", "Примітки"
                ]):
                    item = QTableWidgetItem(str(row[col]) if pd.notna(row[col]) else "")
                    self.inventory_table.setItem(row_idx, col_idx, item)

                    # Підсвітка критичного стану
                    if col == "Цілісність (%)" and pd.notna(row[col]) and int(row[col]) < 20:
                        item.setBackground(QColor(255, 200, 200))  # Світло-червоний
                        critical_count += 1

                if critical_count > 0:
                    logger.warning(f"Виявлено {critical_count} предметів з критичним станом (Цілісність < 20%)")

        except Exception as e:
            logger.error(f"Помилка завантаження даних інвентарю: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані інвентарю: {str(e)}")


    def load_history_data(self):
        """
        Метод для завантаження та відображення історії використання інвентарю.
        Різні статуси оренди підсвічуються різними кольорами.
        """
        logger.info("Завантаження історії використання")

        try:
            base_query = """
                SELECT
                    uh.history_id,
                    i.inventory_number,
                    i.item_name,
                    uh.user_name,
                    uh.start_date,
                    uh.end_date,
                    uh.returned_date,
                    CASE
                        WHEN uh.returned_date IS NULL AND uh.end_date < CURRENT_DATE THEN 'Протерміновано'
                        WHEN uh.returned_date IS NULL THEN 'В оренді'
                        WHEN uh.returned_date > uh.end_date THEN 'Повернено з запізненням'
                        ELSE 'Повернено'
                    END as status,
                    uh.usage_notes
                FROM usage_history uh
                LEFT JOIN inventory i ON uh.item_id = i.item_id
                WHERE uh.is_rental = true
            """

            sort_option = self.history_sort_combo.currentData()
            if sort_option == "start_date_asc":
                base_query += " ORDER BY uh.start_date ASC"
            elif sort_option == "start_date_desc":
                base_query += " ORDER BY uh.start_date DESC"
            elif sort_option == "end_date_asc":
                base_query += " ORDER BY uh.end_date ASC"
            elif sort_option == "end_date_desc":
                base_query += " ORDER BY uh.end_date DESC"
            elif sort_option == "name_asc":
                base_query += " ORDER BY i.item_name ASC"
            elif sort_option == "name_desc":
                base_query += " ORDER BY i.item_name DESC"
            elif sort_option == "user_asc":
                base_query += " ORDER BY uh.user_name ASC"
            elif sort_option == "user_desc":
                base_query += " ORDER BY uh.user_name DESC"
            else:
                base_query += " ORDER BY uh.start_date DESC"

            history_data = self.db.execute_query(base_query, fetch=True, return_df=True)
            logger.debug(f"Отримано {len(history_data)} записів історії використання")

            self.history_table.setRowCount(len(history_data))
            overdue_count = 0
            late_count = 0

            for row_idx, row in history_data.iterrows():
                for col_idx, col in enumerate([
                    "history_id", "inventory_number", "item_name", "user_name",
                    "start_date", "end_date", "returned_date", "status", "usage_notes"
                ]):
                    item = QTableWidgetItem(str(row[col]) if pd.notna(row[col]) else "")
                    self.history_table.setItem(row_idx, col_idx, item)

                    # Підсвітка протермінованих оренд
                status = row['status']
                color = QColor(255, 255, 255)

                if status == 'Протерміновано':
                    color = QColor(255, 200, 200)  # Світло-червоний
                    overdue_count += 1
                elif status == 'Повернено з запізненням':
                    color = QColor(255, 220, 150)  # Світло-оранжевий
                    late_count += 1
                elif status == 'Повернено':
                    color = QColor(200, 255, 200)  # Світло-зелений

                for i in range(self.history_table.columnCount()):
                    item = self.history_table.item(row_idx, 7)
                    if item:  # Перевіряємо, чи існує елемент
                        item.setBackground(color)

            if overdue_count > 0:
                logger.warning(f"Виявлено {overdue_count} протермінованих оренд")
            if late_count > 0:
                logger.warning(f"Виявлено {late_count} повернень з запізненням")

        except Exception as e:
            logger.error(f"Помилка завантаження історії використання: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити історію використання: {str(e)}")

    def clear_history(self):
        """
        Метод для видалення історії використання предметів інвентарю.
        Для підтвердження/скасування дії використовується діалогове вікно.
        """
        logger.warning("Спроба очищення історії використання")

        reply = QMessageBox.question(
            self, "Підтвердження",
            "Ви впевнені, що хочете повністю очистити історію використання?\nЦю дію не можна скасувати!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                logger.info("Підтверджено очищення історії використання")
                if self.db.execute_query("DELETE FROM usage_history"):
                    self.load_history_data()
                    QMessageBox.information(self, "Успіх", "Історію використання успішно очищено")
                    logger.info("Історію використання очищено")
            except Exception as e:
                logger.error(f"Помилка очищення історії використання: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", f"Не вдалося очистити історію: {str(e)}")

    def load_rental_data(self):
        """
        Метод для завантаження та відображення активних оренд.
        Фільтрує записи, показуючи лише активні оренди.
        """
        logger.info("Завантаження даних про активні оренди")
        try:
            rental_data = self.db.get_rental_history()
            logger.debug(f"Отримано {len(rental_data)} записів оренд")

            # Фільтруємо дані - лише оренди без дати повернення
            active_rentals = rental_data[pd.isna(rental_data["Дата повернення"])]
            logger.debug(f"Активних оренд: {len(active_rentals)}")

            self.rental_table.setRowCount(len(active_rentals))
            overdue_count = 0

            for row_idx, (_, row) in enumerate(active_rentals.iterrows()):
                for col_idx, col in enumerate([
                    "ID оренди", "Номер предмету", "Назва предмету",
                    "Орендар", "Початок оренди", "Кінець оренди",
                    "Дата повернення", "Статус оренди", "Примітки"
                ]):
                    item = QTableWidgetItem(str(row[col]) if pd.notna(row[col]) else "")
                    self.rental_table.setItem(row_idx, col_idx, item)

                    # Підсвітка протермінованих оренд
                    if col == "Статус оренди" and row[col] == 'Протерміновано':
                        for i in range(self.rental_table.columnCount()):
                            self.rental_table.item(row_idx, i).setBackground(QColor(255, 200, 200))
                        overdue_count += 1
            if overdue_count > 0:
                logger.warning(f"Активних протермінованих оренд: {overdue_count}")

        except Exception as e:
            logger.error(f"Помилка завантаження даних оренди: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані оренди: {str(e)}")

    def filter_inventory(self):
        """
        Метод для фільтрування таблиці з інвентарем за текстом пошуку та вибраними фільтрами.
        """
        search_text = self.search_input.text().lower()
        category_id = self.category_filter.currentData()
        status_id = self.status_filter.currentData()
        logger.debug(f"Фільтрація інвентарю: пошук='{search_text}', категорія={category_id}, статус={status_id}")

        visible_count = 0
        for row in range(self.inventory_table.rowCount()):
            should_show = True
            item_name = self.inventory_table.item(row, 2).text().lower()
            item_number = self.inventory_table.item(row, 1).text().lower()
            item_category = self.inventory_table.item(row, 3).text()
            item_status = self.inventory_table.item(row, 4).text()

            # Фільтр пошуку
            if search_text and (search_text not in item_name and search_text not in item_number):
                should_show = False

            # Фільтр категорії
            if category_id and item_category != self.category_filter.currentText():
                should_show = False

            # Фільтр статусу
            if status_id and item_status != self.status_filter.currentText():
                should_show = False

            self.inventory_table.setRowHidden(row, not should_show)
            if should_show:
                visible_count += 1

        logger.debug(f"Результат фільтрації інвентарю: показано {visible_count} з {self.inventory_table.rowCount()} записів")

    def filter_history(self):
        """
        Метод для фільтрації таблиці історії пошуку за текстом пошуку та статусом.
        """
        search_text = self.history_search.text().lower()
        logger.debug(f"Фільтрація історії: пошук='{search_text}'")

        visible_count = 0
        for row in range(self.history_table.rowCount()):
            should_show = True
            item_name = self.history_table.item(row, 1).text().lower()
            user_name = self.history_table.item(row, 2).text().lower()

            # Фільтр пошуку
            if search_text and (search_text not in item_name and search_text not in user_name):
                should_show = False

            self.history_table.setRowHidden(row, not should_show)
            if should_show:
                visible_count += 1
        logger.debug(
            f"Результат фільтрації історії використання: показано {visible_count} з {self.history_table.rowCount()} записів")

    def filter_rentals(self):
        """
        Метод для фільтрації таблиці оренди за текстом пошуку та статусом.
        """
        search_text = self.rental_search.text().lower()
        status_filter = self.rental_status_filter.currentData()
        logger.debug(f"Фільтрація оренд: пошук='{search_text}', статус={status_filter}")

        visible_count = 0
        for row in range(self.rental_table.rowCount()):
            should_show = True
            item_name = self.rental_table.item(row, 2).text().lower()
            user_name = self.rental_table.item(row, 3).text().lower()
            status = self.rental_table.item(row, 7).text()

            # Фільтр пошуку
            if search_text and (search_text not in item_name and search_text not in user_name):
                should_show = False

            # Фільтр статусу
            if status_filter == "active" and status != "В оренді":
                should_show = False
            elif status_filter == "returned" and "Повернено" not in status:
                should_show = False
            elif status_filter == "overdue" and status != "Протерміновано":
                should_show = False

            self.rental_table.setRowHidden(row, not should_show)
            if should_show:
                visible_count += 1
        logger.debug(f"Результат фільтрації оренд: показано {visible_count} з {self.rental_table.rowCount()} записів")

    def add_inventory_item(self):
        """
        Відкриває форму для додавання предмета в інвентар.
        Після успішного закінчення операції, оновлює таблицю.
        """
        logger.info("Відкриття форми додавання предмету")

        dialog = InventoryItemForm(self.db)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                item_data = dialog.get_data()
                logger.debug(f"Дані нового предмету: {item_data}")

                item_id = self.db.add_inventory_item(item_data)
                if item_id:
                    self.load_inventory_data()
                    self.status_bar.showMessage("Предмет успішно додано", 3000)
                    logger.info(f"Предмет додано з ID: {item_id}")
            except Exception as e:
                logger.error(f"Помилка додавання предмету: {e}")
                QMessageBox.critical(self, "Помилка", str(e))

    def edit_inventory_item(self):
        """
        Відкриває форму для редагування вибраного предмета інвентарю.
        Після успішного закінчення операції, оновлює таблицю.
        """
        selected_row = self.inventory_table.currentRow()
        if selected_row == -1:
            logger.warning("Спроба редагування без вибору предмету")
            QMessageBox.warning(self, "Попередження", "Будь ласка, виберіть предмет для редагування")
            return

        item_id = int(self.inventory_table.item(selected_row, 0).text())
        item_name = self.inventory_table.item(selected_row, 2).text()

        logger.info(f"Відкриття діалогу редагування предмету: ID={item_id}, назва='{item_name}'")

        dialog = InventoryItemForm(self.db, item_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                item_data = dialog.get_data()
                logger.debug(f"Оновлені дані предмету {item_id}: {item_data}")

                if self.db.update_inventory_item(item_id, item_data):
                    self.load_inventory_data()
                    self.status_bar.showMessage("Предмет успішно оновлено", 3000)
                    logger.info(f"Предмет {item_id} оновлено")
            except Exception as e:
                logger.error(f"Помилка оновлення предмету {item_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", str(e))

    def delete_inventory_item(self):
        """
        Метод для видалення предмета з інвентарю.
        Для підтвердження/скасування дії використовується діалогове вікно.
        """
        selected_row = self.inventory_table.currentRow()
        if selected_row == -1:
            logger.warning("Спроба видалення без вибору предмету")
            QMessageBox.warning(self, "Попередження", "Будь ласка, виберіть предмет для видалення")
            return

        item_id = int(self.inventory_table.item(selected_row, 0).text())
        item_name = self.inventory_table.item(selected_row, 2).text()

        logger.warning(f"Спроба видалення предмету: ID={item_id}, назва='{item_name}'")

        reply = QMessageBox.question(
            self, "Підтвердження",
            f"Ви впевнені, що хочете видалити предмет '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.db.delete_inventory_item(item_id):
                    self.load_inventory_data()
                    self.status_bar.showMessage("Предмет успішно видалено", 3000)
                    logger.info(f"Предмет {item_id} видалено")
            except Exception as e:
                logger.error(f"Помилка видалення предмету {item_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", str(e))

    def rent_item(self):
        """
        Відкриває форму оренди для вибраного предмета.
        Перед відкриттям форми здійснюється перевірка на доступність.
        """
        selected_row = self.inventory_table.currentRow()
        if selected_row == -1:
            logger.warning("Спроба оренди без вибору предмету")
            QMessageBox.warning(self, "Попередження", "Будь ласка, виберіть предмет для оренди")
            return

        item_id = int(self.inventory_table.item(selected_row, 0).text())
        current_status = self.inventory_table.item(selected_row, 4).text()
        item_name = self.inventory_table.item(selected_row, 2).text()

        logger.info(f"Спроба оренди предмету: ID={item_id}, назва='{item_name}', статус='{current_status}'")


        if current_status != "Доступний":
            logger.warning(f"Предмет {item_id} не доступний для оренди: статус '{current_status}'")
            QMessageBox.warning(self, "Попередження", "Цей предмет не доступний для оренди")
            return

        dialog = RentalForm(self.db, item_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                rental_data = dialog.get_data()
                logger.debug(f"Дані оренди предмету {item_id}: {rental_data}")

                if self.db.rent_item(item_id, **rental_data):
                    self.load_inventory_data()
                    self.load_rental_data()
                    self.status_bar.showMessage("Оренду успішно оформлено", 3000)
                    logger.info(f"Оренду предмету {item_id} оформлено")
            except Exception as e:
                logger.error(f"Помилка оформлення оренди предмету {item_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", str(e))

    def return_item(self):
        """
        Відкриває форму повернення з оренди для вибраного предмета.
        """
        selected_row = self.rental_table.currentRow()
        if selected_row == -1:
            logger.warning("Спроба повернення без вибору запису оренди")
            QMessageBox.warning(self, "Попередження", "Будь ласка, виберіть запис оренди")
            return

        rental_id = int(self.rental_table.item(selected_row, 0).text())
        status = self.rental_table.item(selected_row, 7).text()
        item_name = self.rental_table.item(selected_row, 2).text()

        logger.info(f"Спроба повернення предмету з оренди: rental_id={rental_id}, назва='{item_name}', статус='{status}'")

        if "Повернено" in status:
            logger.warning(f"Спроба повернення предмету, якого не було в оренді: rental_id={rental_id}")
            QMessageBox.warning(self, "Попередження", "Цей предмет вже повернено")
            return

        # Отримуємо поточну цілісність предмета
        try:
            item_id = self.db.execute_query(
                "SELECT item_id FROM usage_history WHERE history_id = %s",
                (rental_id,), fetch=True)[0][0]
            logger.debug(f"Знайдено item_id={item_id} для rental_id={rental_id}")

            current_integrity = self.db.execute_query(
                "SELECT integrity_percentage FROM inventory WHERE item_id = %s",
                (item_id,), fetch=True)[0][0]
            logger.debug(f"Поточна цілісність предмета {item_id}: {current_integrity}%")
        except Exception as e:
            logger.error(f"Помилка отримання даних для rental_id={rental_id}: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося отримати дані: {str(e)}")
            return

        dialog = ReturnForm(self.db, rental_id, current_integrity)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                return_data = dialog.get_data()
                logger.debug(f"Дані повернення rental_id={rental_id}: {return_data}")

                if self.db.return_item(
                        rental_id,
                        return_data["returned_date"],
                        return_data["integrity_percentage"],
                        return_data["notes"]
                ):
                    self.load_inventory_data()
                    self.load_rental_data()
                    self.status_bar.showMessage("Повернення успішно зафіксовано", 3000)
                    logger.info(f"Повернення rental_id={rental_id} зафіксовано, нова цілісність: {return_data['integrity_percentage']}%")
            except Exception as e:
                logger.error(f"Помилка фіксації повернення rental_id={rental_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", str(e))

    def apply_styles(self):
        """
        Метод для застосування CSS стилю до всіх елементів інтерфейсу.
        """
        logger.debug("Застосування CSS стилів")

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
                font-family: Arial;
            }
            QTabWidget::pane {
                border: 1px solid #d3d3d3;
                background: white;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #d3d3d3;
                padding: 8px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom-color: white;
                font-weight: bold;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: none;
                selection-background-color: #d1e7ff;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 5px;
                border: 1px solid #d3d3d3;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QLineEdit, QComboBox, QDateEdit {
                padding: 5px;
                border: 1px solid #d3d3d3;
                border-radius: 4px;
                min-height: 25px;
            }
            QStatusBar {
                background-color: #e0e0e0;
                color: #333;
            }
        """)
