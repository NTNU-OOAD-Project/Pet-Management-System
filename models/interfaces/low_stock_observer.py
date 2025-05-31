from abc import ABC, abstractmethod

class low_stock_observer(ABC):
    @abstractmethod
    def notify_low_stock(self, food: str, amount: float):
        pass
