from abc import ABC, abstractmethod
from models.inventory import Inventory

class LowStockObserver(ABC):
    @abstractmethod
    def notify_low_stock(self, inventory: Inventory):
        pass
