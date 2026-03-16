from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QDateEdit, QDialogButtonBox, QMessageBox,
    QLabel, QLineEdit, QSpinBox
)
from PyQt6.QtCore import QDate
import traceback
import logging

logger = logging.getLogger(__name__)


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

        logger.info(f"Ініціалізація форми повернення для оренди з rental_id={rental_id}")

        self.setWindowTitle("Повернення предмету")
        self.setMinimumWidth(400)

        logger.debug(f"Параметри: rental_id={rental_id}, поточна цілісність={current_integrity}%")

        self.init_ui(current_integrity)
        self.load_rental_data()

        logger.info(f"Форму повернення ініціалізовано для оренди з rental_id={rental_id}")

    def init_ui(self, current_integrity):
        """
        Метод для ініціалізації UI форми.
        Створює поля для відображення інформації про оренду, введення дати повернення, нової цілісності
        та приміток.

        :param current_integrity: Цілісність предмета після повернення.
        :type current_integrity: int
        """
        logger.debug("Створення UI форми повернення")

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
        logger.debug(f"Поле 'Дата повернення' створено")

        # Цілісність
        self.integrity_spin = QSpinBox()
        self.integrity_spin.setRange(0, 100)
        self.integrity_spin.setValue(current_integrity)
        self.integrity_spin.setSuffix("%")
        form_layout.addRow("Цілісність предмету:", self.integrity_spin)
        logger.debug(f"Поле 'Цілісність' створено")

        # Примітки
        self.notes_edit = QLineEdit()
        form_layout.addRow("Примітки:", self.notes_edit)
        logger.debug("Поле 'Примітки' створено")


        layout.addLayout(form_layout)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        logger.debug("Кнопки OK та Cancel створено")

    def load_rental_data(self):
        """
        Метод для завантаження та відображення інформації про оренду.
        Показує інформацію про предмет, орендаря та період оренди.

        :raise: Exception, якщо відбулася помилка завантаження.
        """
        logger.info(f"Завантаження даних оренди для rental_id={self.rental_id}")

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
                logger.debug(f"Отримано дані оренди: предмет='{rental_data[1]}', номер='{rental_data[2]}', орендар='{rental_data[3]}'")
                logger.debug(f"Період оренди: {rental_data[4]} - {rental_data[5]}")

                self.rental_info_label.setText(
                    f"Предмет: {rental_data[1]} ({rental_data[2]})\n"
                    f"Орендар: {rental_data[3]}\n"
                    f"Період оренди: {rental_data[4].strftime('%d.%m.%Y')} - {rental_data[5].strftime('%d.%m.%Y')}"
                )

                logger.info(f"Дані оренди {self.rental_id} завантажено")

            else:
                logger.warning(f"Оренду з ID={self.rental_id} не знайдено")
                self.rental_info_label.setText(f"Оренду з ID={self.rental_id} не знайдено")
        except Exception as e:
            logger.error(f"Помилка завантаження даних оренди {self.rental_id}: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """
        Метод для перевірки введених даних.


        :raise: ValueError, якщо введено неправильні дані.
        """
        logger.info("Валідація даних форми повернення")

        try:
            integrity_value = self.integrity_spin.value()
            logger.debug(f"Значення цілісності: {integrity_value}%")

            if integrity_value < 0 or integrity_value > 100:
                logger.warning(f"Валідацію не пройдено: некоректне значення цілісності {integrity_value}%")
                raise ValueError("Цілісність повинна бути від 0 до 100%")

            original_value = self.integrity_spin.property("original_value")
            if original_value and integrity_value < original_value - 20:
                logger.warning(f"Значне погіршення стану предмету: було {original_value}%, стало {integrity_value}%")

            return_date = self.return_date_edit.date()
            logger.debug(f"Дата повернення: {return_date.toString('dd.MM.yyyy')}")

            # Якщо все добре - приймаємо діалог
            logger.info("Валідацію пройдено, форму прийнято")
            self.accept()

        except ValueError as e:
            logger.warning(f"Валідацію не пройдено: {e}")
            QMessageBox.warning(self, "Попередження", str(e))

    def get_data(self):
        """
        Метод для отримання даних у вигляді словника.

        :return: Словник з даними про повернення предмета.
        :rtype: dict
        """
        data = {
            "returned_date": self.return_date_edit.date().toPyDate(),
            "integrity_percentage": self.integrity_spin.value(),
            "notes": self.notes_edit.text().strip()
        }

        logger.debug(f"Зібрані дані повернення: дата={data['returned_date']}, "
                     f"цілісність={data['integrity_percentage']}%, "
                     f"примітки='{data['notes'] if data['notes'] else 'порожньо'}'")

        return data

    def accept(self):
        """Перевизначення методу accept для логування"""
        logger.info(f"Формe повернення для rental_id={self.rental_id} прийнято")
        super().accept()

    def reject(self):
        """Перевизначення методу reject для логування"""
        logger.info(f"Форму повернення для rental_id={self.rental_id} скасовано")
        super().reject()

    def closeEvent(self, event):
        """Обробник закриття вікна"""
        logger.debug(f"Форму повернення для rental_id={self.rental_id} закрито")
        super().closeEvent(event)
