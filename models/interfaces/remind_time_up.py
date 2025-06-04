from abc import ABC, abstractmethod
from reminder.care_reminder import CareReminder

class RemindTimeUp(ABC):
    @abstractmethod
    def remind_time_up(self, care_reminder: CareReminder):
        pass