from abc import ABC, abstractmethod
import pandas as pd

class AbstractDataCollector(ABC):
    """Базовый класс для всех сборщиков данных"""
    @abstractmethod
    def update_config(self, config):
        pass

    @abstractmethod
    def find_objects(self):
        """Найти доступные объекты для мониторинга (например, устройства или клиентов)"""
        pass

    @abstractmethod
    def collect(self, objects=None) -> pd.DataFrame:
        """Собрать данные по выбранным объектам"""
        pass
