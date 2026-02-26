from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from DBConnection import DBConnection


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


        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.tabs = QTabWidget()
        self.tabs.setAccessibleName("Вкладки статистики")
        self.tabs.setAccessibleDescription("Вкладки з різними видами статистичних графіків")

        self.layout.addWidget(self.tabs)

        self.popularity_tab = QWidget()
        self.popularity_tab.setAccessibleName("Графік популярності")
        self.tabs.addTab(self.popularity_tab, "Популярність")
        self.tabs.setTabToolTip(0, "Графік топ-10 найпопулярніших предметів для оренди")
        self.init_popularity_tab()

        self.wear_tab = QWidget()
        self.wear_tab.setAccessibleName("Графік зносу")
        self.tabs.addTab(self.wear_tab, "Знос інвентарю")
        self.tabs.setTabToolTip(1, "Графік топ-10 найбільш зношених предметів")
        self.init_wear_tab()

        self.rental_tab = QWidget()
        self.rental_tab.setAccessibleName("Графік статистики оренди")
        self.tabs.addTab(self.rental_tab, "Статистика оренди")
        self.tabs.setTabToolTip(2, "Статистика оренди по місяцях")
        self.init_rental_tab()

        self.load_data()

    def init_popularity_tab(self):
        """
        Метод для ініціалізації вкладки популярності використання предметів.
        Відображає дані у вигляді стовпчастої діаграми.
        """
        layout = QVBoxLayout()
        self.popularity_tab.setLayout(layout)

        self.popularity_figure = Figure()
        self.popularity_canvas = FigureCanvas(self.popularity_figure)
        self.popularity_canvas.setAccessibleName("Графік популярності")
        self.popularity_canvas.setAccessibleDescription("Стовпчаста діаграма топ-10 найпопулярніших предметів")
        layout.addWidget(self.popularity_canvas)

    def init_wear_tab(self):
        """
        Метод для ініціалізації вкладки зносу предметів.
        Відображає дані у вигляді лінійної діаграми.
        """
        layout = QVBoxLayout()
        self.wear_tab.setLayout(layout)

        self.wear_figure = Figure()
        self.wear_canvas = FigureCanvas(self.wear_figure)
        self.wear_canvas.setAccessibleName("Графік зносу")
        self.wear_canvas.setAccessibleDescription("Горизонтальна діаграма топ-10 найбільш зношених предметів")
        layout.addWidget(self.wear_canvas)

    def init_rental_tab(self):
        """
        Метод для ініціалізації вкладки найбільш орендованих предметів.
        Відображає дані у вигляді стовпчастої діаграми.
        """
        layout = QVBoxLayout()
        self.rental_tab.setLayout(layout)

        self.rental_figure = Figure()
        self.rental_canvas = FigureCanvas(self.rental_figure)
        self.rental_canvas.setAccessibleName("Графік статистики оренди")
        self.rental_canvas.setAccessibleDescription("Стовпчаста діаграма оренди по місяцях")
        layout.addWidget(self.rental_canvas)

    def load_data(self):
        """
        Метод для завантаження всіх статистичних даних.
        """
        self.load_popularity_data()
        self.load_wear_data()
        self.load_rental_stats()

    def load_popularity_data(self):
        """
        Метод для завантаження та відображення даних про популярні предмети.
        Також будує стовпчасту діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        try:
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
                self.popularity_figure.clear()
                ax = self.popularity_figure.add_subplot(111)

                ax.bar(data['item_name'], data['usage_count'])
                ax.set_title('Топ 10 найпопулярніших предметів для оренди')
                ax.set_ylabel('Кількість оренд')
                ax.tick_params(axis='x', rotation=45)
                self.popularity_figure.tight_layout()

                self.popularity_canvas.draw()
        except Exception as e:
            print(f"Помилка завантаження даних популярності: {e}")

    def load_wear_data(self):
        """
        Метод для завантаження та відображення даних про найбільш зношені предмети.
        Також будує лінійну діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        try:
            data = self.db.execute_query("""
                SELECT inv.item_name, inv.integrity_percentage, cnd.condition_name
                FROM inventory inv
                JOIN conditions cnd ON inv.condition_id = cnd.condition_id
                ORDER BY inv.integrity_percentage ASC
                LIMIT 10
            """, fetch=True, return_df=True)

            if not data.empty:
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
        except Exception as e:
            print(f"Помилка завантаження даних зносу: {e}")

    def load_rental_stats(self):
        """
        Метод для завантаження та відображення даних про найбільш популярні предмети для оренди.
        Також будує стовпчасту діаграму для відображення даних.

        :raise: Exception, якщо відбулася помилка завантаження даних.
        """
        try:
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
                self.rental_figure.clear()
                ax = self.rental_figure.add_subplot(111)

                months = ['Січ', 'Лют', 'Бер', 'Кві', 'Тра', 'Чер',
                          'Лип', 'Сер', 'Вер', 'Жов', 'Лис', 'Гру']

                ax.bar(data['month'] - 1, data['rental_count'], label='Всього оренд')
                ax.bar(data['month'] - 1, data['late_count'], label='Запізнілі повернення')
                ax.set_title('Статистика оренди по місяцям')
                ax.set_ylabel('Кількість')
                ax.set_xticks(range(12))
                ax.set_xticklabels(months)
                ax.legend()
                self.rental_figure.tight_layout()

                self.rental_canvas.draw()
        except Exception as e:
            print(f"Помилка завантаження статистики оренди: {e}")