import pickle


class Cache:
    def __init__(self, name):
        self.name = name
        self.data = {}
        self.load()

    def load(self):
        try:
            with open(f"cache/{self.name}.p", 'rb') as f:
                self.data = pickle.load(open(f"cache/{self.name}.p", 'rb'))
        except FileNotFoundError as e:
            print("Error loading file " + str(e))
            pass

    def save(self):
        with open(f"cache/{self.name}.p", 'wb+') as f:
            pickle.dump(self.data, f)

cache = Cache('cache')
cache.load()
cache.save()