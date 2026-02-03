import pandas as pd
import psycopg2


class DBConnection:
    def __init__(self):
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="1234",
                host="localhost"
            )
            return True
        except Exception as e:
            print(f"Помилка підключення до бази даних: {e}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()

    def execute_query(self, query, params=None, fetch=False, return_df=False):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params or ())

                if fetch:
                    if return_df:
                        # Для повернення DataFrame
                        columns = [desc[0] for desc in cursor.description]
                        data = cursor.fetchall()
                        df = pd.DataFrame(data, columns=columns)
                        self.connection.commit()
                        return df
                    else:
                        # Для повернення звичайного результату
                        result = cursor.fetchall()
                        self.connection.commit()
                        return result

                self.connection.commit()
                return True

        except Exception as e:
            self.connection.rollback()
            print(f"Помилка виконання запиту: {e}")
            raise  # Піднімаємо виняток для обробки у викликаючому коді

    def get_categories(self):
        """Отримання списку категорій у вигляді DataFrame"""
        try:
            return self.execute_query(
                "SELECT category_id, category_name FROM categories ORDER BY category_name",
                fetch=True, return_df=True
            )
        except Exception as e:
            raise Exception(f"Не вдалося отримати категорії: {str(e)}")

    def get_statuses(self):
        """Отримання списку статусів у вигляді DataFrame"""
        try:
            return self.execute_query(
                "SELECT status_id, status_name FROM availability_statues ORDER BY status_id",
                fetch=True, return_df=True
            )
        except Exception as e:
            raise Exception(f"Не вдалося отримати статуси: {str(e)}")

    def get_inventory_details(self):
        """Отримання деталей інвентарю з view"""
        try:
            return self.execute_query(
                "SELECT * FROM inventory_details ORDER BY \"ID предмету\"",
                fetch=True, return_df=True
            )
        except Exception as e:
            raise Exception(f"Не вдалося отримати дані інвентарю: {str(e)}")

    def get_rental_history(self):
        """Отримання історії оренди"""
        try:
            return self.execute_query(
                "SELECT * FROM rental_items ORDER BY \"Початок оренди\" DESC",
                fetch=True, return_df=True
            )
        except Exception as e:
            raise Exception(f"Не вдалося отримати історію оренди: {str(e)}")

    def add_inventory_item(self, item_data):
        """Додавання нового предмету інвентарю"""
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
                return result[0][0]  # Повертаємо ID нового предмету
            return None

        except Exception as e:
            raise Exception(f"Не вдалося додати предмет: {str(e)}")

    def update_inventory_item(self, item_id, item_data):
        """Оновлення інформації про предмет інвентарю"""
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

            return self.execute_query(query, params)

        except Exception as e:
            raise Exception(f"Не вдалося оновити предмет: {str(e)}")

    def delete_inventory_item(self, item_id):
        """Видалення предмету інвентарю"""
        try:
            return self.execute_query(
                "DELETE FROM inventory WHERE item_id = %s",
                (item_id,)
            )
        except Exception as e:
            raise Exception(f"Не вдалося видалити предмет: {str(e)}")

    def rent_item(self, item_id, user_name, start_date, end_date, notes):
        """Оренда предмету"""
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
                return result[0][0]  # Повертаємо ID нової оренди
            return None

        except Exception as e:
            raise Exception(f"Не вдалося оформити оренду: {str(e)}")

    def return_item(self, history_id, returned_date, integrity_percentage, notes):
        """Повернення предмету з оренди"""
        try:
            # Спочатку отримуємо ID предмету
            item_query = "SELECT item_id FROM usage_history WHERE history_id = %s"
            item_result = self.execute_query(item_query, (history_id,), fetch=True)
            if not item_result:
                raise Exception("Не знайдено запис оренди")

            item_id = item_result[0][0]

            # Оновлюємо запис оренди
            update_query = """
                UPDATE usage_history SET
                    returned_date = %s,
                    usage_notes = %s
                WHERE history_id = %s
            """

            self.execute_query(update_query, (returned_date, notes, history_id))

            # Оновлюємо цілісність предмета
            integrity_query = """
                UPDATE inventory SET
                    integrity_percentage = %s
                WHERE item_id = %s
            """
            self.execute_query(integrity_query, (integrity_percentage, item_id))

            return True

        except Exception as e:
            raise Exception(f"Не вдалося зафіксувати повернення: {str(e)}")