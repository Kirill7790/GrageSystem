from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QDateEdit,
    QDialogButtonBox, QMessageBox
)

from DBConnection import DBConnection


class InventoryItemForm(QDialog):
    def __init__(self, db: DBConnection, item_id=None):
        super().__init__()
        self.db = db
        self.item_id = item_id
        self.setWindowTitle("Додати новий предмет" if not item_id else "Редагувати предмет")
        self.setMinimumWidth(400)

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Форма для введення даних
        form_layout = QFormLayout()

        # Назва предмету
        self.item_name_edit = QLineEdit()
        form_layout.addRow("Назва предмету:", self.item_name_edit)

        # Категорія
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.lineEdit().setPlaceholderText("Введіть або виберіть категорію")

        # Додаємо існуючі категорії
        try:
            categories = self.db.get_categories()
            self.category_combo.addItem("")  # Порожній елемент
            for _, row in categories.iterrows():
                self.category_combo.addItem(row['category_name'])
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))

        form_layout.addRow("Категорія:", self.category_combo)

        # Статус
        self.status_combo = QComboBox()
        try:
            statuses = self.db.get_statuses()
            for _, row in statuses.iterrows():
                self.status_combo.addItem(row['status_name'], row['status_id'])
        except Exception as e:
            QMessageBox.critical(self, "Помилка", str(e))
        form_layout.addRow("Статус:", self.status_combo)

        # Цілісність
        self.integrity_spin = QSpinBox()
        self.integrity_spin.setRange(0, 100)
        self.integrity_spin.setSuffix("%")
        form_layout.addRow("Цілісність:", self.integrity_spin)

        # Дата поступлення
        self.purchase_date_edit = QDateEdit()
        self.purchase_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.purchase_date_edit.setDate(QDate.currentDate())
        self.purchase_date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата поступлення:", self.purchase_date_edit)

        # Примітки
        self.notes_edit = QLineEdit()
        form_layout.addRow("Примітки:", self.notes_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_data(self):
        """Завантаження даних для редагування"""
        if self.item_id is not None:
            try:
                query = """
                    SELECT i.item_name, i.category_id, i.status_id, 
                           i.integrity_percentage, i.purchase_date, i.item_notes
                    FROM inventory i
                    WHERE i.item_id = %s
                """
                result = self.db.execute_query(query, (self.item_id,), fetch=True)

                if result:
                    item_data = result[0]
                    self.item_name_edit.setText(item_data[0])

                    # Встановлення категорії
                    index = self.category_combo.findData(item_data[1])
                    if index >= 0:
                        self.category_combo.setCurrentIndex(index)

                    # Встановлення статусу
                    index = self.status_combo.findData(item_data[2])
                    if index >= 0:
                        self.status_combo.setCurrentIndex(index)

                    self.integrity_spin.setValue(item_data[3])

                    # Встановлення дати
                    if item_data[4]:
                        self.purchase_date_edit.setDate(item_data[4])

                    self.notes_edit.setText(item_data[5] if item_data[5] else "")

            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """Перевірка даних перед закриттям діалогу"""
        try:
            # Перевіряємо обов'язкові поля
            if not self.item_name_edit.text().strip():
                raise ValueError("Введіть назву предмету")

            category_name = self.category_combo.currentText().strip()
            if not category_name:
                raise ValueError("Введіть назву категорії")

            # Перевіряємо чи категорія вже існує
            category_id = self.get_or_create_category(category_name)
            if not category_id:
                raise ValueError("Не вдалося визначити категорію")

            # Якщо все добре - приймаємо діалог
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Попередження", str(e))

    def get_or_create_category(self, category_name):
        """Отримує ID категорії або створює нову"""
        try:
            # Спочатку пробуємо знайти існуючу категорію
            result = self.db.execute_query(
                "SELECT category_id FROM categories WHERE category_name = %s",
                (category_name,), fetch=True)

            if result:  # Категорія існує
                return result[0][0]

            # Якщо категорії немає - створюємо нову
            result = self.db.execute_query(
                "INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id",
                (category_name,), fetch=True)

            if result:
                return result[0][0]

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Помилка роботи з категоріями: {str(e)}")
        return None

    def get_data(self):
        """Повертає дані у вигляді словника"""
        category_name = self.category_combo.currentText().strip()
        category_id = self.get_or_create_category(category_name)
        return {
            "item_name": self.item_name_edit.text().strip(),
            "category_id": category_id,
            "status_id": self.status_combo.currentData(),
            "integrity_percentage": self.integrity_spin.value(),
            "purchase_date": self.purchase_date_edit.date().toPyDate(),
            "item_notes": self.notes_edit.text().strip()
        }