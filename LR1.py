class Symbol:
    def __init__(self, name: str):
        self.name = name

class NonTerminateSymbol(Symbol):
    first_set = []
    follow_set = []

    def __init__(self, name):
        super(NonTerminateSymbol, self).__init__(name)


class TerminateSymbol(Symbol):
    def __init__(self, name):
        super(TerminateSymbol, self).__init__(name)