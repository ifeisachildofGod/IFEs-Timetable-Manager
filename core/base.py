
import random

from enum import Enum
from copy import deepcopy
from typing import Callable


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


class HooksManagerError(TypeError):
    pass

class Signal(Enum):
    SubjectAdd = "SubjectAdd"
    ClassLevelAdd = "ClassLevelAdd"
    ClassAdd = "ClassRemove"
    
    SubjectRemove = "SubjectRemove"
    ClassLevelRemove = "ClassLevelRemove"
    ClassRemove = "ClassRemove"
    
    def __add__(self, other):
        return Signal(self.value + (other.value if isinstance(other, Signal) else str(other)), self.name + (other.name if isinstance(other, Signal) else str(other)))

    def __radd__(self, other):
        return self.__add__(other)

class SignalType(Enum):
    SOURCE = "SOURCE"
    RECIEVER = "RECIEVER"


class _ConnectionsManager:
    def __init__(self):
        self.dynamicID = None
        self.connections_blocked = False
        
        self.connections_tracker = {}
    
    def blockAll(self, state: bool):
        self.connections_blocked = state
    
    def blockConnection(self, name: str, state: bool):
        self.connections_tracker[name][1] = state
    
    def setDynamicID(self, id: ID):
        self.dynamicID = id
    
    def _useDynamicID(self):
        dyID = self.dynamicID
        self.dynamicID = None
        
        return dyID
    
    def _doMasterConnection(self, name: str, func_output):
        if not self.connections_blocked and name in self.connections_tracker:
            connections, block_state = self.connections_tracker[name]
            
            if not block_state:
                for conn in connections:
                    if isinstance(func_output, tuple):
                        conn_params = func_output
                    elif func_output is None:
                        conn_params = []
                    else:
                        conn_params = [func_output]
                    
                    conn(*conn_params)
    
    def _addConnection(self, name, func: Callable):
        if name not in self.connections_tracker:
            self.connections_tracker[name] = [], False
        
        self.connections_tracker[name][0].append(func)


class Hyperlink:
    def __init__(self, name: Signal | str, signal_type: SignalType, is_dynamic: bool | None = None):
        self.name = name
        self.signal_type = signal_type
        self.is_dynamic = is_dynamic if is_dynamic is not None else False
    
    def __call__(self, func):
        self.func = func
        self.wrapper = None
        
        if self.signal_type == SignalType.SOURCE:
            def wrapper(*args, **kwargs):
                func_output = self.func(*args, **kwargs)
                
                CONNECTIONS_MANAGER._doMasterConnection(self.name + (CONNECTIONS_MANAGER._useDynamicID() if self.is_dynamic else ""), func_output)
                
                return func_output
            
            self.wrapper = wrapper
        
        elif self.signal_type == SignalType.RECIEVER:
            self.wrapper = self.func
            
            CONNECTIONS_MANAGER._addConnection(self.name, self.func)
        
        return self
    
    def __set_name__(self, owner, name):
        prev_init = deepcopy(owner.__init__)
        
        def new_init(instance, *args, **kwargs):
            prev_init(instance, *args, **kwargs)
            
            if self.signal_type == SignalType.RECIEVER:
                name = self.name
                
                if self.is_dynamic and (id := CONNECTIONS_MANAGER._useDynamicID()) is not None:
                    name = self.name + id
                    
                    CONNECTIONS_MANAGER._addConnection(name, self.func)
                
                connections = CONNECTIONS_MANAGER.connections_tracker[name][0]
                
                new_func = lambda *args, **kwargs: self.func(instance, *args, **kwargs)
                
                if self.func in connections:
                    connections[connections.index(self.func)] = new_func
                else:
                    connections.append(new_func)
        
        owner.__init__ = new_init
    
    def __get__(self, instance, owner):
        func = lambda *args, **kwargs: self.wrapper(instance, *args, **kwargs)
        
        if self.signal_type == SignalType.RECIEVER:
            connections = CONNECTIONS_MANAGER.connections_tracker[self.name][0]
            connections[connections.index(self.func)] = func
        
        return func
    
    @staticmethod
    def setDynamicID(id: ID):
        CONNECTIONS_MANAGER.setDynamicID(id)


CONNECTIONS_MANAGER = _ConnectionsManager()


if __name__ == "__main__":
    class Obj1:
        @Hyperlink("FirstTest", SignalType.SOURCE, True)
        def test_source(self):
            return "ife"

    class Obj2:
        def __init__(self, name: str):
            self.name = name
        
        @Hyperlink("FirstTest", SignalType.RECIEVER, True)
        def test_connection(self, expectation):
            print(self.name, expectation)

    b = Obj1()

    Hyperlink.setDynamicID("123")
    a = Obj2("Ify")
    Hyperlink.setDynamicID("123")
    c = Obj2("Mama")


    Hyperlink.setDynamicID("123")
    b.test_source()

