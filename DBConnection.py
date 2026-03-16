import traceback

import pandas as pd
import psycopg2
import logging


logger = logging.getLogger(__name__)

class DBConnection:
    """
    Клас, що відповідає за підключення до бази даних та здійснення запитів до неї

    Attributes:
        connection: Об'єкт підключення до бази даних
    """

    def __init__(self):
        """
        Метод для ініціалізації об'єкта DBConnection зі значенням підключення none.
        """
        self.connection = None

    def connect(self):
        """
        Метод для встановлення підключення до бази даних.

        :return:
            True у випадку успішного підключення, False у випадку помилки.
        :rtype: bool
        """
        try:
            self.connection = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="1234",
                host="localhost"
            )
            logger.info("Підключення до БД встановлено")
            return True
        except Exception as e:
            logger.error(f"Помилка підключення до БД: {e}" )
            print(f"Помилка підключення до бази даних: {e}")
            return False

    def disconnect(self):
        """
        Метод для закриття підключення до бази даних.

        Якщо підключення було відкрите, метод закриває його.
        """
        if self.connection:
            self.connection.close()
            logger.info("Підключення до БД завершено")

    def execute_query(self, query, params=None, fetch=False, return_df=False):
        """
        Метод для виконання запиту до бази даних.

        :param query: Запит мовою SQL.
        :type query: str

        :param params: Параметри для підставлення в запит.
        :type params: tuple, optional

        :param fetch: Чи потрібно повертати результат запиту.
        :type fetch: bool

        :param return_df: Чи необхідно повертати результат у вигляді DataFrame.
        :type return_df: bool

        :return:
            * Якщо fetch = False: True при успішному виконанні.
            * Якщо fetch = True та return_df = False: Список кортежів з результатами.
            * Якщо fetch = True та return_df = True: DataFrame з результатами запиту.
        """
        short_query = query[:100] + "..." if len(query) > 100 else query
        logger.info(f"SQL Query: {short_query}")

        if params:
            logger.debug(f"Параметри запиту: {params}")

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())

                if fetch:
                    if return_df:
                        # Для повернення DataFrame
                        logger.debug("Повернення результату як DataFrame")
                        columns = [desc[0] for desc in cursor.description]
                        data = cursor.fetchall()
                        df = pd.DataFrame(data, columns=columns)
                        self.connection.commit()
                        logger.info(f"Отримано {len(df)} рядків даних")
                        return df
                    else:
                        # Для повернення звичайного результату
                        result = cursor.fetchall()
                        self.connection.commit()
                        logger.info(f"Отримано {len(result)} рядків")
                        return result

                self.connection.commit()
                logger.info(f"Змінено {cursor.rowcount} рядків")
                return True

        except Exception as e:
            self.connection.rollback()
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            print(f"Помилка виконання запиту: {e}")
            raise  # Піднімаємо виняток для обробки у викликаючому коді

    def get_categories(self):
        """Метод для отримання всіх категорій інвентарю з бази даних

        :return: DataFrame з колонками category_id та category_name.
        :rtype: pandas.DataFrame

        :raise: Exception, якщо відбулася помилка отримання даних.
        """
        logger.info("Запит на отримання списку категорій")
        try:
            result = self.execute_query(
                "SELECT category_id, category_name FROM categories ORDER BY category_name",
                fetch=True, return_df=True
            )
            logger.debug(f"Отримано {len(result)} категорій")
            return result
        except Exception as e:
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося отримати категорії: {str(e)}")

    def get_statuses(self):
        """
        Метод для отримання всіх статусів доступності інвентарю з бази даних.

        :return: DataFrame з колонками status_id та status_name.
        :rtype: pandas.DataFrame

        :raise: Exception, якщо відбулася помилка отримання даних.
        """
        logger.info("Запит на отримання списку статусів")
        try:
            result =  self.execute_query(
                "SELECT status_id, status_name FROM availability_statues ORDER BY status_id",
                fetch=True, return_df=True
            )
            logger.debug(f"Отримано {len(result)} статусів")
            return result
        except Exception as e:
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося отримати статуси: {str(e)}")

    def get_inventory_details(self):
        """
        Метод для отримання детальної інформації про інвентар з view.

        :return: DataFrame з детальною інформацією про інвентар.
        :rtype: pandas.DataFrame

        :raise: Exception, якщо відбулася помилка отримання даних.
        """
        logger.info("Запит на отримання списку інвентарю")
        try:
            result = self.execute_query(
                "SELECT * FROM inventory_details ORDER BY \"ID предмету\"",
                fetch=True, return_df=True
            )
            logger.debug(f"Отримано {len(result)} рядків предметів")
            return result
        except Exception as e:
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося отримати дані інвентарю: {str(e)}")

    def get_rental_history(self):
        """
        Метод для отримання історії оренд інвентарю з бази даних.

        :return: DataFrame з історією оренди, відсортованою за датою початку.
        :rtype: pandas.DataFrame

        :raise: Exception, якщо відбулася помилка отримання даних.
        """
        logger.info("Запит на отримання історії використання")
        try:
            result = self.execute_query(
                "SELECT * FROM rental_items ORDER BY \"Початок оренди\" DESC",
                fetch=True, return_df=True
            )
            logger.debug(f"Отримано {len(result)} рядків історії використання")
            return result
        except Exception as e:
            logger.error(f"Помилка виконання запиту: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося отримати історію оренди: {str(e)}")

    def add_inventory_item(self, item_data):
        """
        Метод для додавання предметів в інвентар.

        :param item_data: Словник з даними предмету.
        Словник складається з наступних частин:
            - item_name: Назва предмету
            - category_id: ID категорії
            - status_id: ID статусу
            - integrity_percentage: Відсоток цілісності
            - purchase_date: Дата придбання
            - item_notes: Примітки
        :type item_data: dict

        :return: ID новоствореного предмету або None при помилці.
        :rtype: int

        :raise: Exception, якщо відбулася помилка додавання даних.
        """
        logger.info(f"Додавання нового предмету: {item_data.get('item_name')}")
        logger.debug(f"Дані предмету: {item_data}")

        try:
            # Категорія вже повинна бути створена на цей момент
            query = """
                INSERT INTO inventory (
                    item_name, category_id, status_id,
                    integrity_percentage, purchase_date, item_notes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING item_id
            """
            params = (
                item_data["item_name"], item_data["category_id"], item_data["status_id"],
                item_data["integrity_percentage"], item_data["purchase_date"],
                item_data["item_notes"]
            )

            result = self.execute_query(query, params, fetch=True)
            if result:
                item_id = result[0][0]
                logger.info(f"Предмет додано успішно з ID: {item_id}")
                return item_id # Повертаємо ID нового предмету
            logger.warning("Предмет додано, але ID не отримано")
            return None

        except Exception as e:
            logger.error(f"Помилка при додаванні предмету: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося додати предмет: {str(e)}")

    def update_inventory_item(self, item_id, item_data):
        """
        Метод для оновлення чинного інвентарю.

        :param item_id: ID предмету, який планується оновити
        :type item_id: int

        :param item_data: Словник з новими даними предмета.
        :type item_data: int

        :return: True при успішному оновленні, False - при невдалому.
        :rtype: bool

        :raise: Exception, якщо відбулася помилка оновлення даних.
        """
        logger.info(f"Оновлення предмету з ID: {item_id}")
        logger.debug(f"Нові дані: {item_data}")

        try:
            query = """
                UPDATE inventory SET
                    item_name = %s,
                    category_id = %s,
                    status_id = %s,
                    integrity_percentage = %s,
                    purchase_date = %s,
                    item_notes = %s
                WHERE item_id = %s
            """
            params = (
                item_data["item_name"], item_data["category_id"], item_data["status_id"],
                item_data["integrity_percentage"], item_data["purchase_date"],
                item_data["item_notes"], item_id
            )

            result = self.execute_query(query, params)
            logger.info(f"Предмет з ID {item_id} оновлено успішно")
            return result

        except Exception as e:
            logger.error(f"Помилка при оновленні предмету {item_id}: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося оновити предмет: {str(e)}")

    def delete_inventory_item(self, item_id):
        """
        Метод для видалення чинних предметів з інвентарю.

        :param item_id: ID предмета, який необхідно видалити.
        :type item_id: int

        :return: True при успішному видаленні, False - при невдалому.
        :rtype: bool

        :raise: Exception, якщо відбулася помилка видалення даних.
        """
        logger.warning(f"Видалення предмету з ID: {item_id}")

        try:
            result = self.execute_query(
                "DELETE FROM inventory WHERE item_id = %s",
                (item_id,)
            )
            logger.info(f"Предмет з ID {item_id} видалено")
            return result
        except Exception as e:
            logger.error(f"Помилка при видаленні предмету {item_id}: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося видалити предмет: {str(e)}")

    def rent_item(self, item_id, user_name, start_date, end_date, notes):
        """
        Метод для оформлення оренди конкретного предмета з інвентарю.

        :param item_id: ID предмету для оренди.
        :type item_id: int

        :param user_name: Ім'я орендаря.
        :type user_name: str

        :param start_date: Дата початку оренди.
        :type start_date: date

        :param end_date: Дата кінця оренди.
        :type end_date: date

        :param notes: Нотатки.
        :type notes: str

        :return: ID новоствореного запису оренди.
        :rtype: int

        :raise: Exception, якщо виникла помилка оформлення оренди.
        """
        logger.info(f"Оформлення оренди: предмет {item_id}, орендар {user_name}")
        logger.debug(f"Дата початку: {start_date}, дата завершення: {end_date}")

        try:
            query = """
                INSERT INTO usage_history (
                    item_id, user_name, start_date, end_date,
                    returned_date, usage_notes, is_rental
                ) VALUES (%s, %s, %s, %s, NULL, %s, true)
                RETURNING history_id
            """
            params = (item_id, user_name, start_date, end_date, notes)

            result = self.execute_query(query, params, fetch=True)
            if result:
                history_id = result[0][0] # Повертаємо ID нової оренди
                logger.info(f"Оренду оформлено з ID: {history_id}")
                return history_id
            return None

        except Exception as e:
            logger.error(f"Помилка при оформленні оренди: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося оформити оренду: {str(e)}")

    def return_item(self, history_id, returned_date, integrity_percentage, notes):
        """
        Метод для оформлення повернення предмета з оренди.

        :param history_id: ID запису оренди.
        :type history_id: int

        :param returned_date: Дата повернення предмета з оренди.
        :type returned_date: date

        :param integrity_percentage: Цілісність предмета після повернення з оренди.
        :type integrity_percentage: int

        :param notes: Нотатки
        :type notes: str

        :return: True при успішному поверненні предмета з оренди.
        :rtype: bool

        :raise: Exception, якщо виникла помилка повернення предмета з оренди.
        """
        logger.info(f"Повернення предмету з оренди ID: {history_id}")
        logger.debug(f"Новий стан цілісності: {integrity_percentage}%")

        try:
            # Спочатку отримуємо ID предмету
            item_query = "SELECT item_id FROM usage_history WHERE history_id = %s"
            item_result = self.execute_query(item_query, (history_id,), fetch=True)
            if not item_result:
                logger.error(f"Не знайдено запис оренди з ID {history_id}")
                raise Exception("Не знайдено запис оренди")

            item_id = item_result[0][0]
            logger.debug(f"ID предмету: {item_id}")

            # Оновлюємо запис оренди
            update_query = """
                UPDATE usage_history SET
                    returned_date = %s,
                    usage_notes = %s
                WHERE history_id = %s
            """

            self.execute_query(update_query, (returned_date, notes, history_id))
            logger.debug("Запис оренди оновлено")

            # Оновлюємо цілісність предмета
            integrity_query = """
                UPDATE inventory SET
                    integrity_percentage = %s
                WHERE item_id = %s
            """
            self.execute_query(integrity_query, (integrity_percentage, item_id))
            logger.debug("Цілісність предмета оновлено")

            return True

        except Exception as e:
            logger.error(f"Помилка при поверненні предмету: {e}")
            logger.error(f"Деталі:\n{traceback.format_exc()}")
            raise Exception(f"Не вдалося зафіксувати повернення: {str(e)}")
