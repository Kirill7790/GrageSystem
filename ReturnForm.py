from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QDateEdit, QDialogButtonBox, QMessageBox,
    QLabel, QLineEdit, QSpinBox
)
from PyQt6.QtCore import QDate


class ReturnForm(QDialog):
    """
    Клас, що відповідає за форму повернення предмета з оренди.
    """
    def __init__(self, db, rental_id, current_integrity):
        """
        Метод для ініціалізації форми повернення предмета з оренди.

        :param db: Підключення до бази даних.
        :type db: DBConnection

        :param rental_id: ID запису оренди.
        :type rental_id: int

        :param current_integrity: Цілісність предмета після повернення.
        :type current_integrity: int
        """
        super().__init__()
        self.db = db
        self.rental_id = rental_id
        self.setWindowTitle("Повернення предмету")
        self.setMinimumWidth(400)

        self.init_ui(current_integrity)
        self.load_rental_data()

    def init_ui(self, current_integrity):
        """
        Метод для ініціалізації UI форми.
        Створює поля для відображення інформації про оренду, введення дати повернення, нової цілісності
        та приміток.

        :param current_integrity: Цілісність предмета після повернення.
        :type current_integrity: int
        """
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Інформація про оренду
        self.rental_info_label = QLabel()
        layout.addWidget(self.rental_info_label)

        # Форма для введення даних
        form_layout = QFormLayout()

        # Дата повернення
        self.return_date_edit = QDateEdit()
        self.return_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.return_date_edit.setDate(QDate.currentDate())
        self.return_date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата повернення:", self.return_date_edit)

        # Цілісність
        self.integrity_spin = QSpinBox()
        self.integrity_spin.setRange(0, 100)
        self.integrity_spin.setValue(current_integrity)
        self.integrity_spin.setSuffix("%")
        form_layout.addRow("Цілісність предмету:", self.integrity_spin)

        # Примітки
        self.notes_edit = QLineEdit()
        form_layout.addRow("Примітки:", self.notes_edit)

        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_rental_data(self):
        """
        Метод для завантаження та відображення інформації про оренду.
        Показує інформацію про предмет, орендаря та період оренди.

        :raise: Exception, якщо відбулася помилка завантаження.
        """
        try:
            query = """
                SELECT r.history_id, i.item_name, i.inventory_number, 
                       r.user_name, r.start_date, r.end_date
                FROM usage_history r
                JOIN inventory i ON r.item_id = i.item_id
                WHERE r.history_id = %s AND r.is_rental = true
            """
            result = self.db.execute_query(query, (self.rental_id,), fetch=True)

            if result:
                rental_data = result[0]
                self.rental_info_label.setText(
                    f"Предмет: {rental_data[1]} ({rental_data[2]})\n"
                    f"Орендар: {rental_data[3]}\n"
                    f"Період оренди: {rental_data[4].strftime('%d.%m.%Y')} - {rental_data[5].strftime('%d.%m.%Y')}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """
        Метод для перевірки введених даних.


        :raise: ValueError, якщо введено неправильні дані.
        """
        try:
            if self.integrity_spin.value() < 0 or self.integrity_spin.value() > 100:
                raise ValueError("Цілісність повинна бути від 0 до 100%")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Попередження", str(e))

    def get_data(self):
        """
        Метод для отримання даних у вигляді словника.

        :return: Словник з даними про повернення предмета.
        :rtype: dict
        """
        return {
            "returned_date": self.return_date_edit.date().toPyDate(),
            "integrity_percentage": self.integrity_spin.value(),
            "notes": self.notes_edit.text().strip()
        }