class Transactions(list):
    def __init__(self, category, source):
        self.category = category
        self.source = source
        super().__init__()
