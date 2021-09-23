from models.data import Data


class Report(Data):
    def __init__(self, data):
        super().__init__()

        self.of = data["of"]
        self.reason = data["reason"]
        self.reporter = data["reporter"]
        self.description = data["description"]
