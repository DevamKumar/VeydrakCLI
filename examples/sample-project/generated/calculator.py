class Calculator:
    def __init__(self):
        self.history = []

    def add(self, a, b):
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result

    def subtract(self, a, b):
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result

    def multiply(self, a, b):
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        result = a / b
        self.history.append(f"divide({a}, {b}) = {result}")
        return result

    def get_history(self):
        return self.history
