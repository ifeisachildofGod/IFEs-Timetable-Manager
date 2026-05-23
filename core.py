
import random


class ID(str):
    def __init__(self):
        super().__init__()
    
    def __add__(self, value):
        return ID(f"{self}->{value}")
    
    @staticmethod
    def generate_new():
        tmp = random.randint()
        
        return ID(id(tmp))

