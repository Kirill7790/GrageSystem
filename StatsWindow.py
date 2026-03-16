from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from DBConnection import DBConnection
import logging
import traceback

logger = logging.getLogger(__name__)

class StatsWindow(QWidget):
    """
    Клас, що відповідає за вкладку статистики використання інвентарю.

    В собі містить три наступних вкладки:
        - Вкладка "Популярність"
        - Вкладка "Знос"
        - Вкладка "Статистика оренд"
    """
    def __init__(self, db: DBConnection, parent=None):
        """
        Метод для ініціалізації вкладки зі статистикою використання предметів.

        :param db: Підключення до бази даних.
        :type db: DBConnection

        :param parent: Батьківська вкладка.
        """
        super().__init__(parent)
        self.db = db

        logger.info("Ініціалізація вкладки статистики")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("Вкладки статистики")
        self.tabs.setAccessibleDescription("Вкладки з різними видами статистичних графіків")

        self.layout.addWidget(self.tabs)
        logger.debug("Створено віджети вкладок")

        self.popularity_tab = QWidget()
        self.popularity_tab.setAccessibleName("Графік популярності")
        self.tabs.addTab(self.popularity_tab, "Популярність")
        self.tabs.setTabToolTip(0, "Графік топ-10 найпопулярніших предметів для оренди")
        self.init_popularity_tab()
        logger.debug("Вкладку 'Популярність' створено")

        self.wear_tab = QWidget()
        self.wear_tab.setAccessibleName("Графік зносу")
        self.tabs.addTab(self.wear_tab, "Знос інвентарю")
        self.tabs.setTabToolTip(1, "Графік топ-10 найбільш зношених предметів")
        self.init_wear_tab()
        logger.debug("Вкладку 'Знос інвентарю' створено")

        self.rental_tab = QWidget()
        self.rental_tab.setAccessibleName("Графік статистики оренди")
        self.tabs.addTab(self.rental_tab, "Статистика оренди")
        self.tabs.setTabToolTip(2, "Статистика оренди по місяцях")
        self.init_rental_tab()
        logger.debug("Вкладку 'Статистика оренди' створено")

        logger.info("Завантаження даних для статистики")
        self.load_data()

        logger.info("Вікно статистики успішно ініціалізовано")

    def init_popularity_tab(self):
        """
        Метод для ініціалізації вкладки популярності використання предметів.
        Відображає дані у вигляді стовпчастої діаграми.
        """
        logger.debug("Ініціалізація вкладки популярності предметів")

        layout = QVBoxLayout()
        self.popularity_tab.setLayout(layout)

        self.popularity_figure = Figure()
        self.popularity_canvas = FigureCanvas(self.popularity_figure)
        self.popularity_canvas.setAccessibleName("Графік популярності")
        self.popularity_canvas.setAccessibleDescription("Стовпчаста діаграма топ-10 найпопулярніших предметів")
        layout.addWidget(self.popularity_canvas)
        logger.debug("Створено графік популярності предметів")

    def init_wear_tab(self):
        """
        Метод для ініціалізації вкладки зносу предметів.
        Відображає дані у вигляді лінійної діаграми.
        """
        logger.debug("Ініціалізація вкладки зносу")

        layout = QVBoxLayout()
        self.wear_tab.setLayout(layout)

        self.wear_figure = Figure()
        self.wear_canvas = FigureCanvas(self.wear_figure)
        self.wear_canvas.setAccessibleName("Графік зносу")
        self.wear_canvas.setAccessibleDescription("Горизонтальна діаграма топ-10 найбільш зношених предметів")
        layout.addWidget(self.wear_canvas)
        logger.debug("Створено графік зносу предметів")

    def init_rental_tab(self):
        """
        Метод для ініціалізації вкладки найбільш орендованих предметів.
        Відображає дані у вигляді стовпчастої діаграми.
        """
        logger.debug("Ініціалізація вкладки статистики оренди предметів")

        layout = QVBoxLayout()
        self.rental_tab.setLayout(layout)

        self.rental_figure = Figure()
        self.rental_canvas = FigureCanvas(self.rental_figure)
        self.rental_canvas.setAccessibleName("Графік статистики оренди")
        self.rental_canvas.setAccessibleDescription("Стовпчаста діаграма оренди по місяцях")
        layout.addWidget(self.rental_canvas)
        logger.debug("Створено графік статистики оренди предметів")

    def load_data(self):
        """
        Метод для завантаження всіх статистичних даних.
        """
        logger.info("Завантаження статистичних даних")

        self.load_popularity_data()
        self.load_wear_data()
        self.load_rental_stats()

        logger.info("Успішне завантаження всіх статистичних даних")

    def load_popularity_data(self):
        """
        Метод для завантаження та відображення даних про популярні предмети.
        Також будує стовпчасту діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        logger.info("Завантаження даних популярності предметів")

        try:
            logger.debug("Виконання SQL запиту для вкладки 'Популярність'")
            data = self.db.execute_query("""
                SELECT inv.item_name, COUNT(uh.history_id) as usage_count
                FROM inventory inv
                LEFT JOIN usage_history uh on inv.item_id = uh.item_id
                WHERE uh.is_rental = true
                GROUP BY inv.item_id
                ORDER BY usage_count DESC
                LIMIT 10
            """, fetch=True, return_df=True)

            if not data.empty:
                logger.info(f"Отримано дані про {len(data)} найпопулярніших предметів")
                logger.debug(f"Топ-5 предметів: {data['item_name'].head(5).tolist()}")

                total_rentals = data['usage_count'].sum()
                logger.debug(f"Загальна кількість оренд топ-10 предметів: {total_rentals}")

                self.popularity_figure.clear()
                ax = self.popularity_figure.add_subplot(111)

                bars = ax.bar(data['item_name'], data['usage_count'])
                ax.set_title('Топ 10 найпопулярніших предметів для оренди')
                ax.set_ylabel('Кількість оренд')
                ax.tick_params(axis='x', rotation=45)

                # Додаємо значення над стовпчиками
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{int(height)}', ha='center', va='bottom')

                self.popularity_figure.tight_layout()
                self.popularity_canvas.draw()

                logger.info("Графік популярності успішно оновлено")
            else:
                logger.warning("Немає даних для відображення графіка популярності")

        except Exception as e:
            logger.error(f"Помилка завантаження даних популярності: {e}")
            logger.debug(traceback.format_exc())
            print(f"Помилка завантаження даних популярності: {e}")

    def load_wear_data(self):
        """
        Метод для завантаження та відображення даних про найбільш зношені предмети.
        Також будує лінійну діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        logger.info("Завантаження даних про знос інвентарю")

        try:
            logger.debug("Виконання SQL запиту для вкладки зносу")
            data = self.db.execute_query("""
                SELECT inv.item_name, inv.integrity_percentage, cnd.condition_name
                FROM inventory inv
                JOIN conditions cnd ON inv.condition_id = cnd.condition_id
                ORDER BY inv.integrity_percentage ASC
                LIMIT 10
            """, fetch=True, return_df=True)

            if not data.empty:
                logger.info(f"Отримано дані про {len(data)} найбільш зношених предметів")

                self.wear_figure.clear()
                ax = self.wear_figure.add_subplot(111)

                bars = ax.barh(data['item_name'], data['integrity_percentage'])
                ax.set_title('Топ 10 найбільш зношених речей')
                ax.set_xlabel('Цілісність (у %)')
                ax.set_xlim(0, 100)

                for i, (bar, condition) in enumerate(zip(bars, data['condition_name'])):
                    width = bar.get_width()
                    ax.text(width + 2, bar.get_y() + bar.get_height() / 2,
                            condition, ha='left', va='center')

                self.wear_figure.tight_layout()
                self.wear_canvas.draw()
            else:
                logger.warning("Немає даних для відображення графіка зносу")
        except Exception as e:
            logger.error(f"Помилка завантаження даних зносу: {e}")
            logger.debug(traceback.format_exc())
            print(f"Помилка завантаження даних зносу: {e}")

    def load_rental_stats(self):
        """
        Метод для завантаження та відображення даних про найбільш популярні предмети для оренди.
        Також будує стовпчасту діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        logger.info("Завантаження даних про статистику оренди")

        try:
            logger.debug("Виконання SQL запиту для вкладки 'Статистика оренди'")
            data = self.db.execute_query("""
                SELECT
                    EXTRACT(MONTH FROM start_date) as month,
                    COUNT(*) as rental_count,
                    COUNT(CASE WHEN returned_date > end_date THEN 1 END) as late_count
                FROM usage_history
                WHERE is_rental = true
                GROUP BY month
                ORDER BY month
            """, fetch=True, return_df=True)

            if not data.empty:
                logger.info(f"Отримано статистику за {len(data)} місяців")

                logger.info(f"Отримано статистику за {len(data)} місяців")

                total_rentals = data['rental_count'].sum()
                total_late = data['late_count'].sum()
                late_percentage = (total_late / total_rentals * 100) if total_rentals > 0 else 0

                logger.info(
                    f"Загальна статистика: {total_rentals} оренд, {total_late} запізнень ({late_percentage:.1f}%)")

                # Знаходимо місяць з найбільшою кількістю оренд
                max_rental_month = data.loc[data['rental_count'].idxmax()]
                logger.debug(
                    f"Піковий місяць: {int(max_rental_month['month'])} з {max_rental_month['rental_count']} орендами")

                self.rental_figure.clear()
                ax = self.rental_figure.add_subplot(111)

                months = ['Січ', 'Лют', 'Бер', 'Кві', 'Тра', 'Чер',
                          'Лип', 'Сер', 'Вер', 'Жов', 'Лис', 'Гру']

                # Переконуємось що всі місяці присутні
                month_data = {int(m): {'rental': 0, 'late': 0} for m in range(1, 13)}
                for _, row in data.iterrows():
                    month_data[int(row['month'])]['rental'] = row['rental_count']
                    month_data[int(row['month'])]['late'] = row['late_count']

                rental_values = [month_data[m]['rental'] for m in range(1, 13)]
                late_values = [month_data[m]['late'] for m in range(1, 13)]

                bars1 = ax.bar(range(12), rental_values, label='Всього оренд', alpha=0.7)
                bars2 = ax.bar(range(12), late_values, label='Запізнілі повернення', alpha=0.7)

                ax.set_title('Статистика оренди по місяцям')
                ax.set_ylabel('Кількість')
                ax.set_xticks(range(12))
                ax.set_xticklabels(months)
                ax.legend()

                # Додаємо значення
                for bars in [bars1, bars2]:
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(bar.get_x() + bar.get_width() / 2., height,
                                    f'{int(height)}', ha='center', va='bottom', fontsize=8)

                self.rental_figure.tight_layout()
                self.rental_canvas.draw()

                logger.info("Графік статистики оренди успішно оновлено")
            else:
                logger.warning("Немає даних для відображення статистики оренди")
        except Exception as e:
            logger.error(f"Помилка завантаження статистики оренди: {e}")
            logger.debug(traceback.format_exc())
            print(f"Помилка завантаження статистики оренди: {e}")
