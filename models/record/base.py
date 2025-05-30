from datetime import datetime
from abc import ABC, abstractmethod

class Record(ABC):
    _id_counter = 1

    def __init__(self, date=None):
        self.id = Record._id_counter
        Record._id_counter += 1
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
