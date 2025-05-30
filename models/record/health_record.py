from models.record.base import Record

class HealthRecord(Record):
    def __init__(self, details, vaccine, treatment, date=None):
        super().__init__(date)
        self.details = details
        self.vaccine = vaccine
        self.treatment = treatment

    def view_record(self):
        return f"{self.date} 健康紀錄: {self.details}, 疫苗: {self.vaccine}, 治療: {self.treatment}"

    def update_record(self, details=None, vaccine=None, treatment=None):
        if details:
            self.details = details
        if vaccine:
            self.vaccine = vaccine
        if treatment:
            self.treatment = treatment

    def to_dict(self):
        return {
            "id": self.id,
            "type": "health",
            "date": self.date.isoformat(),
            "details": self.details,
            "vaccine": self.vaccine,
            "treatment": self.treatment
        }
