
# from imports import *
from utils.data import Signal, SignalType
from typing import Any, Callable


class HooksManagerError(TypeError):
    pass

class _ConnectionsManager:
    def __init__(self):
        self.connections_blocked = False
        
        self.connections_tracker = {}
    
    def blockAll(self, state: bool):
        self.connections_blocked = state
    
    def blockConnection(self, name: str, state: bool):
        self.connections_tracker[name][1] = state
    
    def setVar(self, var: Any):
        self.var = var
    
    def resetVar(self):
        del self.var
    
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


class Hook:
    def __init__(self, name: Signal | str, signal_type: SignalType):
        self.name = name
        self.signal_type = signal_type
    
    def __call__(self, func):
        self.func = func
        self.wrapper = None
        
        if self.signal_type == SignalType.SOURCE:
            def wrapper(*args, **kwargs):
                func_output = self.func(*args, **kwargs)
                
                CONNECTIONS_MANAGER._doMasterConnection(self.name, func_output)
                
                return func_output
            
            self.wrapper = wrapper
        
        elif self.signal_type == SignalType.RECIEVER:
            self.wrapper = self.func
            
            CONNECTIONS_MANAGER._addConnection(self.name, self.func)
        
        return self
    
    def __set_name__(self, owner, name):
        if self.signal_type == SignalType.RECIEVER:
            connections = CONNECTIONS_MANAGER.connections_tracker[self.name][0]
            
            func = connections[connections.index(self.func)]
            connections[connections.index(self.func)] = lambda *args, **kwargs: func(owner, *args, **kwargs)
    
    def __get__(self, instance, owner):
        func = lambda *args, **kwargs: self.wrapper(instance, *args, **kwargs)
        
        if self.signal_type == SignalType.RECIEVER:
            connections = CONNECTIONS_MANAGER.connections_tracker[self.name][0]
            connections[connections.index(self.func)] = func
            
        return func
    
    def _process_conn_params(self, conn_params: str):
        signal_type, signal_name = conn_params.strip().split(">")
        signal_type = signal_type.strip().lower() ; signal_name = signal_name.strip()
        
        match signal_type:
            case "source":
                signal_type = SignalType.SOURCE
            case "recv":
                signal_type = SignalType.RECIEVER
            case _:
                raise HooksManagerError(f"Invalid signal type: {signal_type}")
        
        return signal_type, signal_name


CONNECTIONS_MANAGER = _ConnectionsManager()


# class Test:
#     @Hook("FirstTest", SignalType.SOURCE)
#     def test_source(self):
#         return "ife"

# class Test2:
#     @Hook("FirstTest", SignalType.RECIEVER)
#     def test_connection(self, expectation):
#         print(expectation)


# Test().test_source()

# a = Test2()
