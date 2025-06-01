from abc import ABC, abstractmethod
from datetime import datetime

class Record(ABC):
    def __init__(self, date=None):
        self.date = date or datetime.now()

    @abstractmethod
    def view_record(self):
        pass

    @abstractmethod
    def update_record(self, **kwargs):
        pass

    @abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict):
        pass
