class Calculator:
    def __init__(self, value):
        self.value = value

    def add(self, number):
        return self.value + number

    def square(self):
        return self.value * self.value