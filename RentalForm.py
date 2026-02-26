from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QDialogButtonBox,
    QMessageBox, QLabel
)

from DBConnection import DBConnection


class RentalForm(QDialog):
    """
    Клас, що відповідає за форму оренди предмета інвентарю.
    """
    def __init__(self, db: DBConnection, item_id=None):
        """
        Метод для ініціалізації вікна оренди.

        :param db: Підключення до бази даних.
        :type db: DBConnection

        :param item_id: ID предмета для оренди.
        :type item_id: int, optional
        """
        super().__init__()
        self.db = db
        self.item_id = item_id
        self.setWindowTitle("Оренда предмету" if item_id else "Повернення предмету")
        self.setMinimumWidth(400)

        self.init_ui()
        self.load_item_data()

    def init_ui(self):
        """
        Метод для ініціалізації UI форми.
        Створює поля для введення імені орендаря, дати початку/кінця оренди, приміток.
        """
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Інформація про предмет
        self.item_info_label = QLabel()
        layout.addWidget(self.item_info_label)

        # Форма для введення даних
        form_layout = QFormLayout()

        # Ім'я орендаря
        self.user_name_edit = QLineEdit()
        form_layout.addRow("Ім'я орендаря:", self.user_name_edit)

        # Дата початку оренди
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("Початок оренди:", self.start_date_edit)

        # Дата кінця оренди
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("Кінець оренди:", self.end_date_edit)

        # Примітки
        self.notes_edit = QLineEdit()
        form_layout.addRow("Примітки:", self.notes_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_item_data(self):
        """
        Метод для завантаження та відображення інформації про предмет для оренди.
        Показує номер, назву та статус предмета.

        :raise: Exception, якщо виникла помилка завантаження даних.
        """
        if self.item_id is not None:
            try:
                query = """
                    SELECT i.inventory_number, i.item_name, s.status_name
                    FROM inventory i
                    JOIN availability_statues s ON i.status_id = s.status_id
                    WHERE i.item_id = %s
                """
                result = self.db.execute_query(query, (self.item_id,), fetch=True)

                if result:
                    item_data = result[0]
                    self.item_info_label.setText(
                        f"Предмет: {item_data[1]} ({item_data[0]})\n"
                        f"Статус: {item_data[2]}"
                    )

            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """
        Метод для перевірки введених даних.

        :raise: ValueError, якщо введено некоректні дані.
        """
        try:
            # Перевірка заповненості обов'язкових полів
            if not self.user_name_edit.text().strip():
                raise ValueError("Введіть ім'я орендаря")

            if self.start_date_edit.date() > self.end_date_edit.date():
                raise ValueError("Дата початку не може бути пізніше дати кінця")

            # Якщо все добре - приймаємо діалог
            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Попередження", str(e))

    def get_data(self):
        """
        Метод для отримання даних у вигляді словника.

        :return: Словник з даними оренди.
        :rtype: dict
        """
        return {
            "user_name": self.user_name_edit.text().strip(),
            "start_date": self.start_date_edit.date().toPyDate(),
            "end_date": self.end_date_edit.date().toPyDate(),
            "notes": self.notes_edit.text().strip()
        }