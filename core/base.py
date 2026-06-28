import random

class ID(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.parents = []
    
    def __add__(self, value):
        id = ID(value)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    def __radd__(self, other):
        return self.__add__(other)
    
    @staticmethod
    def generate_new():
        tmp = random.randint(0, 500000)
        
        return ID(id(tmp))

class SavedState:
    def __init__(self):
        self.saved = False
    
    def save(self):
        self.saved = True
    
    def unsave(self):
        self.saved = False
    
    def isSaved(self):
        self.saved = True
        
SAVED_STATE = SavedState()

