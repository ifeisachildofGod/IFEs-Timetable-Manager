import random

class ID(str):
    def __init__(self, *args, **kwargs):
        super().__init__()
        
        self.parents: list[ID] = []
    
    def __add__(self, value):
        id = ID(value)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    def __radd__(self, other):
        return self.__add__(other)
    
    def __sub__(self, other):
        if self == other:
            id = self.parents[-1]
        else:
            self.parents.remove(other)
            
            for p in self.parents:
                if p.parents == self.parents:
                    id = p
                    break
            else:
                id = self
        
        return id
    
    def __rsub__(self, other):
        return self.__sub__(other)
    
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

