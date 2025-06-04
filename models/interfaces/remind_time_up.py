from abc import ABC, abstractmethod
from models.record.remind_record import CareReminderRecord

class RemindTimeUp(ABC):
    @abstractmethod
    def remind_time_up(self, care_reminder: CareReminderRecord):
        pass
