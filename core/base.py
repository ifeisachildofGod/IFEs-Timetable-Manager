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
    def new():
        tmp = random.randint(0, 500000)
        
        return ID(id(tmp))

class CLASS_ID(ID):
    def __init__(self, *args, class_level_id: ID = None, **kwargs):
        super().__init__(*args, **kwargs)
        
        assert class_level_id is not None
        
        self.class_level_id = class_level_id
    
    def __add__(self, value):
        if isinstance(value, CLASS_ID):
            assert self.class_level_id == value.class_level_id
        
        id = CLASS_ID(value, class_level_id=self.class_level_id)
        
        id.parents = self.parents.copy()
        id.parents.append(self)
        
        return id
    
    @staticmethod
    def new(class_level_id):
        tmp = random.randint(0, 500000)
        
        return CLASS_ID(id(tmp), class_level_id=class_level_id)



