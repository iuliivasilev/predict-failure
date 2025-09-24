from abc import ABC, abstractmethod
import pandas as pd

class AbstractModel(ABC):
    """Базовый класс для ML-моделей (в т.ч. survival)"""

    @abstractmethod
    def fit(self, data: pd.DataFrame):
        """Обучить модель (если нужно)"""
        pass

    @abstractmethod
    def predict(self, data: pd.DataFrame):
        """Сделать прогноз (например, функция выживания, риск)"""
        pass
