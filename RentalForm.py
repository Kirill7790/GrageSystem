import traceback

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDateEdit, QDialogButtonBox,
    QMessageBox, QLabel
)

import logging
from DBConnection import DBConnection

logger = logging.getLogger(__name__)

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

        mode = "оренди" if item_id else "повернення"
        logger.info(f"Ініціалізація форми {mode}")
        self.setWindowTitle("Оренда предмету" if item_id else "Повернення предмету")
        self.setMinimumWidth(400)

        logger.debug(f"Параметри: item_id={item_id}, режим={mode}")

        self.init_ui()
        self.load_item_data()

        logger.info(f"Форму {mode} ініціалізовано")

    def init_ui(self):
        """
        Метод для ініціалізації UI форми.
        Створює поля для введення імені орендаря, дати початку/кінця оренди, приміток.
        """
        logger.debug(f"Створення UI форми оренди/повернення")

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
        logger.debug("Поле 'Ім'я орендаря' створено")

        # Дата початку оренди
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.start_date_edit.setDate(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        form_layout.addRow("Початок оренди:", self.start_date_edit)
        logger.debug(f"Поле 'Початок оренди' створено")

        # Дата кінця оренди
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.end_date_edit.setDate(QDate.currentDate().addDays(7))
        self.end_date_edit.setCalendarPopup(True)
        form_layout.addRow("Кінець оренди:", self.end_date_edit)
        logger.debug(
            f"Поле 'Кінець оренди' створено")

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

    def load_item_data(self):
        """
        Метод для завантаження та відображення інформації про предмет для оренди.
        Показує номер, назву та статус предмета.

        :raise: Exception, якщо виникла помилка завантаження даних.
        """
        if self.item_id is not None:
            logger.info(f"Завантаження даних предмету з ID={self.item_id} для оренди")

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
                    logger.debug(f"Отримано дані предмету: номер='{item_data[0]}', назва='{item_data[1]}', статус='{item_data[2]}'")


                    self.item_info_label.setText(
                        f"Предмет: {item_data[1]} ({item_data[0]})\n"
                        f"Статус: {item_data[2]}"
                    )
                    if item_data[2] != "Доступний":
                        logger.warning(f"Предмет {self.item_id} має статус '{item_data[2]}', а не 'Доступний'")

                    logger.info(f"Дані предмету {self.item_id} завантажено")

                else:
                    logger.warning(f"Предмет з ID={self.item_id} не знайдено в базі даних")
                    self.item_info_label.setText(f"Предмет з ID={self.item_id} не знайдено")

            except Exception as e:
                logger.error(f"Помилка завантаження даних предмету з ID= {self.item_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """
        Метод для перевірки введених даних.

        :raise: ValueError, якщо введено некоректні дані.
        """
        logger.info("Валідація даних форми")

        try:
            # Перевірка заповненості обов'язкових полів
            user_name = self.user_name_edit.text().strip()
            if not user_name:
                logger.warning("Валідацію не пройдено: порожнє ім'я орендаря")
                raise ValueError("Введіть ім'я орендаря")
            logger.debug(f"Ім'я орендаря: '{user_name}'")

            start_date = self.start_date_edit.date()
            end_date = self.end_date_edit.date()

            logger.debug(f"Дата початку: {start_date.toString('dd.MM.yyyy')}")
            logger.debug(f"Дата кінця: {end_date.toString('dd.MM.yyyy')}")

            if start_date > end_date:
                logger.warning(f"Валідацію не пройдено: дата початку {start_date.toString('dd.MM.yyyy')} пізніше дати кінця {end_date.toString('dd.MM.yyyy')}")
                raise ValueError("Дата початку не може бути пізніше дати кінця")

            if start_date < QDate.currentDate():
                logger.warning(f"Дата початку {start_date.toString('dd.MM.yyyy')} знаходиться в минулому")

            # Якщо все добре - приймаємо діалог
            logger.info("Валідація успішна, форму прийнято")
            self.accept()

        except ValueError as e:
            logger.warning(f"Валідацію не пройдено: {e}")
            QMessageBox.warning(self, "Попередження", str(e))

    def get_data(self):
        """
        Метод для отримання даних у вигляді словника.

        :return: Словник з даними оренди.
        :rtype: dict
        """
        data = {
            "user_name": self.user_name_edit.text().strip(),
            "start_date": self.start_date_edit.date().toPyDate(),
            "end_date": self.end_date_edit.date().toPyDate(),
            "notes": self.notes_edit.text().strip()
        }

        logger.debug(f"Зібрані дані оренди: орендар='{data['user_name']}', "
                     f"початок={data['start_date']}, "
                     f"кінець={data['end_date']}, "
                     f"примітки='{data['notes'] if data['notes'] else 'порожньо'}'")

        return data

    def accept(self):
        """Перевизначення методу accept для логування"""
        logger.info(f"Форма оренди предмету з ID= {self.item_id} прийнята")
        super().accept()

    def reject(self):
        """Перевизначення методу reject для логування"""
        logger.info(f"Форма оренди предмету з ID= {self.item_id} скасована")
        super().reject()

    def closeEvent(self, event):
        """Обробник закриття вікна"""
        logger.debug(f"Форма оренди предмету з ID= {self.item_id} закривається")
        super().closeEvent(event)