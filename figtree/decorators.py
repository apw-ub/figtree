"""
Decorators for class configurations
"""

def group(name = None):
    def decorator(function):
        function._group_name = name if name != None else function.__name__
        return function
    return decorator