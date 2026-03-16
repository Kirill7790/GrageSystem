import traceback

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QDateEdit,
    QDialogButtonBox, QMessageBox
)
import logging
from DBConnection import DBConnection

logger = logging.getLogger(__name__)

class InventoryItemForm(QDialog):
    """
    Клас, що відповідає за форму створення або редагування предметів інвентарю.
    """
    def __init__(self, db: DBConnection, item_id=None):
        """
        Метод для ініціалізації вікна форми.

        :param db: Підключення для бази даних.
        :type db: DBConnection

        :param item_id: ID предмета для редагування (None для нового предмета).
        :type item_id: int, optional
        """
        super().__init__()
        self.db = db
        self.item_id = item_id

        mode = "редагування" if item_id else "додавання"
        logger.info(f"Ініціалізація форми {mode} предмету")
        self.setWindowTitle("Додати новий предмет" if not item_id else "Редагувати предмет")
        self.setMinimumWidth(400)

        logger.debug(f"Параметри: item_id={item_id}, режим={mode}")

        self.init_ui()
        self.load_data()

        logger.info(f"Форму {mode} предмету ініціалізовано")

    def init_ui(self):
        """
        Метод для ініціалізації UI форми. Створює поля для введення інформації користувачем.
        """
        layout = QVBoxLayout()
        self.setLayout(layout)
        logger.debug("Створення UI форми")

        # Форма для введення даних
        form_layout = QFormLayout()

        # Назва предмету
        self.item_name_edit = QLineEdit()
        form_layout.addRow("Назва предмету:", self.item_name_edit)
        logger.debug("Поле 'Назва предмету' створено")

        # Категорія
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.lineEdit().setPlaceholderText("Введіть або виберіть категорію")
        logger.debug("Поле 'Категорія' створено")

        # Додаємо існуючі категорії
        try:
            logger.info("Завантаження списку категорій")
            categories = self.db.get_categories()
            self.category_combo.addItem("")  # Порожній елемент
            for _, row in categories.iterrows():
                self.category_combo.addItem(row['category_name'])
            logger.debug(f"Завантажено {len(categories)} категорій")
        except Exception as e:
            logger.error(f"Помилка завантаження категорій: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", str(e))

        form_layout.addRow("Категорія:", self.category_combo)

        # Статус
        self.status_combo = QComboBox()
        try:
            logger.info("Завантаження списку статусів")
            statuses = self.db.get_statuses()
            for _, row in statuses.iterrows():
                self.status_combo.addItem(row['status_name'], row['status_id'])
            logger.debug(f"Завантажено {len(statuses)} статусів")
        except Exception as e:
            logger.error(f"Помилка завантаження статусів: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            QMessageBox.critical(self, "Помилка", str(e))
        form_layout.addRow("Статус:", self.status_combo)

        # Цілісність
        self.integrity_spin = QSpinBox()
        self.integrity_spin.setRange(0, 100)
        self.integrity_spin.setSuffix("%")
        form_layout.addRow("Цілісність:", self.integrity_spin)
        logger.debug("Поле 'Цілісність' створено")

        # Дата поступлення
        self.purchase_date_edit = QDateEdit()
        self.purchase_date_edit.setDisplayFormat("dd.MM.yyyy")
        self.purchase_date_edit.setDate(QDate.currentDate())
        self.purchase_date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата входу на склад:", self.purchase_date_edit)
        logger.debug(f"Поле 'Дата входу на склад' створено")

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

    def load_data(self):
        """
        Метод для завантаження даних (у випадку редагування).
        Наявні поля заповнюються даними з бази.
        """
        if self.item_id is not None:
            logger.info(f"Завантаження даних для редагування предмету з ID={self.item_id}")

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
                    logger.debug(f"Отримано дані предмету: назва='{item_data[0]}', цілісність={item_data[3]}%")
                    self.item_name_edit.setText(item_data[0])
                    logger.debug(f"Встановлено назву: {item_data[0]}")

                    # Встановлення категорії
                    index = self.category_combo.findData(item_data[1])
                    if index >= 0:
                        self.category_combo.setCurrentIndex(index)
                        logger.debug(f"Встановлено категорію з ID={item_data[1]}")
                    else:
                        logger.warning(f"Категорію з ID={item_data[1]} не знайдено в списку")

                    # Встановлення статусу
                    index = self.status_combo.findData(item_data[2])
                    if index >= 0:
                        self.status_combo.setCurrentIndex(index)
                        logger.debug(f"Встановлено статус з ID={item_data[2]}")
                    else:
                        logger.warning(f"Статус з ID={item_data[2]} не знайдено в списку")

                    self.integrity_spin.setValue(item_data[3])
                    logger.debug(f"Встановлено цілісність: {item_data[3]}%")

                    # Встановлення дати
                    if item_data[4]:
                        self.purchase_date_edit.setDate(item_data[4])
                        logger.debug(f"Встановлено дату надходження: {item_data[4]}")

                    notes = item_data[5] if item_data[5] else ""
                    self.notes_edit.setText(notes)
                    logger.debug(f"Встановлено примітки: {notes if notes else 'порожньо'}")

                    logger.info(f"Дані для редагування предмету {self.item_id} завантажено")
                else:
                    logger.warning(f"Предмет з ID={self.item_id} не знайдено в базі даних")

            except Exception as e:
                logger.error(f"Помилка завантаження даних предмету {self.item_id}: {e}")
                logger.error(f"Деталі:\n{traceback.format_exc()}")
                QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {str(e)}")

    def validate_and_accept(self):
        """
        Метод для перевірки коректності введених даних.

        :raise: ValueError, якщо введено некоректні дані.
        """
        logger.info("Валідація даних форми")
        try:
            # Перевіряємо обов'язкові поля
            item_name = self.item_name_edit.text().strip()
            if not item_name:
                logger.warning("Валідація не пройдена: порожня назва предмету")
                raise ValueError("Введіть назву предмету")
            logger.debug(f"Назва предмету: '{item_name}'")

            category_name = self.category_combo.currentText().strip()
            if not category_name:
                logger.warning("Валідацію не пройдено: порожня категорія")
                raise ValueError("Введіть назву категорії")
            logger.debug(f"Категорія: '{category_name}'")

            # Перевіряємо чи категорія вже існує
            logger.debug(f"Пошук/створення категорії '{category_name}'")
            category_id = self.get_or_create_category(category_name)
            if not category_id:
                logger.error(f"Не вдалося отримати ID для категорії '{category_name}'")
                raise ValueError("Не вдалося визначити категорію")
            logger.debug(f"Отримано category_id={category_id}")

            integrity_value = self.integrity_spin.value()
            logger.debug(f"Цілісність: {integrity_value}%")

            if integrity_value < 20:
                logger.warning(f"Предмет має критичний рівень цілісності: {integrity_value}%")

            # Якщо все добре - приймаємо діалог
            logger.info("Валідація пройшла успішно, форму прийнято")
            self.accept()

        except ValueError as e:
            logger.warning(f"Валідацію не пройдено: {e}")
            QMessageBox.warning(self, "Попередження", str(e))

    def get_or_create_category(self, category_name):
        """
        Метод для отримання або створення категорії.

        :param category_name: Назва категорії.
        :type category_name: str

        :return: ID категорії.
        """
        logger.debug(f"Обробка категорії: '{category_name}'")

        try:
            # Спочатку пробуємо знайти існуючу категорію
            logger.debug(f"Пошук існуючої категорії '{category_name}'")
            result = self.db.execute_query(
                "SELECT category_id FROM categories WHERE category_name = %s",
                (category_name,), fetch=True)

            if result: # Категорія існує
                category_id = result[0][0]
                logger.debug(f"Знайдено існуючу категорію '{category_name}' з ID={category_id}")
                return category_id

            # Якщо категорії немає - створюємо нову
            logger.info(f"Створення нової категорії: '{category_name}'")
            result = self.db.execute_query(
                "INSERT INTO categories (category_name) VALUES (%s) RETURNING category_id",
                (category_name,), fetch=True)

            if result:
                category_id = result[0][0]
                logger.info(f"Створено нову категорію '{category_name}' з ID={category_id}")
                return category_id

            logger.error(f"Не вдалося створити категорію '{category_name}' - немає результату")
            return None

        except Exception as e:
            logger.error(f"Помилка роботи з категоріями для '{category_name}': {e}")
            QMessageBox.critical(self, "Помилка", f"Помилка роботи з категоріями: {str(e)}")
        return None

    def get_data(self):
        """
        Метод для отримання даних у вигляді словника.

        :return: Словник з даними предмету.
        :rtype: dict
        """
        category_name = self.category_combo.currentText().strip()
        logger.debug(f"Отримання даних з форми для категорії '{category_name}'")

        category_id = self.get_or_create_category(category_name)
        data = {
            "item_name": self.item_name_edit.text().strip(),
            "category_id": category_id,
            "status_id": self.status_combo.currentData(),
            "integrity_percentage": self.integrity_spin.value(),
            "purchase_date": self.purchase_date_edit.date().toPyDate(),
            "item_notes": self.notes_edit.text().strip()
        }

        logger.debug(f"Зібрані дані: назва='{data['item_name']}', "
                     f"category_id={data['category_id']}, "
                     f"status_id={data['status_id']}, "
                     f"цілісність={data['integrity_percentage']}%, "
                     f"дата={data['purchase_date']}, "
                     f"примітки='{data['item_notes'] if data['item_notes'] else 'порожньо'}'")

        return data

    def accept(self):
        """Перевизначення методу accept для логування"""
        mode = "редагування" if self.item_id else "додавання"
        logger.info(f"Форма {mode} предмету прийнята")
        super().accept()

    def reject(self):
        """Перевизначення методу reject для логування"""
        mode = "редагування" if self.item_id else "додавання"
        logger.info(f"Форма {mode} предмету скасована")
        super().reject()

    def closeEvent(self, event):
        """Обробник закриття вікна"""
        mode = "редагування" if self.item_id else "додавання"
        logger.debug(f"Форма {mode} предмету закривається")
        super().closeEvent(event)
