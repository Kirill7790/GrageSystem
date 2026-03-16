import logging
import logging.config
from pathlib import Path

# Створюємо директорію для логів
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    # Форматери для різних типів повідомлень
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'db_format': {
            'format': '%(asctime)s - [DB] - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'inventory_format': {
            'format': '%(asctime)s - [INVENTORY] - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'form_format': {
            'format': '%(asctime)s - [FORM] - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'main_format': {
            'format': '%(asctime)s - [MAIN] - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'stats_format': {
            'format': '%(asctime)s - [STATS] - %(levelname)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s - %(message)s'
        }
    },

    # Обробники логів
    'handlers': {
        # Консольний вивід
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },

        # Загальний файл для всіх логів
        'file_common': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': 'logs/application.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Файл для помилок
        'file_errors': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'logs/errors.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для DBconnection
        'file_db': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'db_format',
            'filename': 'logs/db_connection.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для InventoryApp
        'file_inventory': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'inventory_format',
            'filename': 'logs/inventory_app.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для InventoryItemForm
        'file_inventory_form': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'form_format',
            'filename': 'logs/inventory_item_form.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для RentalForm
        'file_rental': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'form_format',
            'filename': 'logs/rental_form.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для ReturnForm
        'file_return': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'form_format',
            'filename': 'logs/return_form.log',
            'mode': 'a',
            'encoding': 'utf-8'
        },

        # Окремий файл для StatsWindow
        'file_stats': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'stats_format',
            'filename': 'logs/stats_window.log',
            'mode': 'a',
            'encoding': 'utf-8'
        }
    },

    # Логери для кожного модуля
    'loggers': {
        # Кореневий логер
        '': {
            'handlers': ['console', 'file_common', 'file_errors'],
            'level': 'INFO',
            'propagate': True
        },

        # Логер для DBconnection
        'DBconnection': {
            'handlers': ['file_db', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },

        # Логер для InventoryApp
        'InventoryApp': {
            'handlers': ['file_inventory', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },

        # Логер для InventoryItemForm
        'InventoryItemForm': {
            'handlers': ['file_inventory_form', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },

        # Логер для Main
        'Main': {
            'handlers': ['console', 'file_common', 'file_errors'],
            'level': 'INFO',
            'propagate': False
        },

        # Логер для RentalForm
        'RentalForm': {
            'handlers': ['file_rental', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },

        # Логер для ReturnForm
        'ReturnForm': {
            'handlers': ['file_return', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        },

        # Логер для StatsWindow
        'StatsWindow': {
            'handlers': ['file_stats', 'file_common', 'file_errors'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}


def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)