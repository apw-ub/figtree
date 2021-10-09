import os
import sys
import inspect
import importlib

FIGTREE_NAMES = ["_group_name", "group"]

def is_path_dir(path):
    """
    Description:
    Check if all of `path` is a directory.

    Input:
        path: str - Config path.

    Output:
        is_dir: bool - True if full path of `path` is directory, else False.
        partial_dir: str - Part of `path` that is a directory path.
    """
    if os.path.isdir(path):
        return True, None
    
    directories = path.split("/")[::-1]
    for index, _ in enumerate(directories):
        dir_path = "/".join(directories[index:][::-1])
        if os.path.isdir(dir_path):
            return False, dir_path

    raise NotADirectoryError(f"Could not find '{ path }', expected directory '{ directories[-1] }'")


def is_path_py(path, partial_path = None): 
    """
    Description:
    Check if part of `path` is a Python file.

    Input:
        path: str - Config path.
        partial_path: str - Part of path that is a filesystem directory.

    Output:
        is_py: bool - True if Python file is part of `path`, else False.
        py_file: str - Name of the Python file.
    """
    if partial_path == None:
        return False, None

    py_file = path[len(partial_path):].split("/")[1]

    if os.path.isfile(partial_path + "/" + py_file + ".py"):
        return True, py_file
    
    raise FileNotFoundError(f"Could not find '{ path }', expected '{ py_file }.py' file")


def is_path_class(path, partial_dir = None, py_file = None, reset = False):
    """
    Description:
    Check if part of `path` is a Python file.

    Input:
        path: str - Config path.
        partial_path: str - Part of path that is a filesystem directory.
        py_file: str: Name of the Python file.
        reset: bool: Reloads the config (updates cache).

    Output:
        is_class: bool - True if part of `path` is class object, else False.
        classes: dict - Returns dict file with first layer of classes.
    """
    if partial_dir == None:
         return False, None

    pyfile_path = partial_dir + "/" + py_file
    module_name = (pyfile_path).replace("/", ".")

    _mod = import_module(module_name, reset)
    _mod_dict = module_as_dict(_mod)
    _variables = list(_mod_dict.keys())

    if path == pyfile_path:
        return False, _mod_dict

    class_path = path[len(pyfile_path):].split("/")[1:]

    _class = _mod
    for cls_obj in class_path:

        _class_vars = [var for var in _variables if isinstance(_class.__dict__[var], type)]

        var_name = None
        for var in _class_vars:
            try:
                if cls_obj == _class.__dict__[var]._group_name:
                    var_name = var
                    break
            except:
                pass

        if var_name == None and cls_obj in _class_vars:
            _class = _class.__dict__[cls_obj]
            _variables = [attr for attr in dir(_class) if not attr.startswith("__")] 
        elif var_name:
            _class = _class.__dict__[var]
            _variables = [attr for attr in dir(_class) if not attr.startswith("__")] 
        else:
            raise NotImplementedError(f"Could not find '{ path }', expected class object '{ cls_obj }'")

    return True, {k:v for k, v in _class.__dict__.items() if not k.startswith("__") and k not in FIGTREE_NAMES}


def import_module(name, reload = False):
    """
    Import/reloads module.
    """
    try:
        if reload:
            module = importlib.reload(sys.modules[name])
        else:
            raise
    except:
        module = importlib.import_module(name)

    return module


def module_as_dict(module):
    """
    Returns module contents as dict object.
    """
    def try_group_name(attr):
        try:
            return module.__dict__[attr]._group_name
        except:
            return attr

    variables = [attr for attr in dir(module) if not attr.startswith("__") and attr not in FIGTREE_NAMES]
    return {try_group_name(attr): module.__dict__[attr] for attr in variables}


def inherited_class_as_dict(class_obj):
    """
    Returns class contents as dict object.
    """
    def try_group_name(attr):
        try:
            return class_vars[attr]._group_name
        except:
            return attr

    class_vars = {}
    for order in class_obj.__mro__[::-1]:
        if "__dict__" in dir(order):
            var_dict = {k:v for k, v in order.__dict__.items() if not k.startswith("__") and k not in FIGTREE_NAMES}
            class_vars = {**class_vars, **var_dict}

    return {try_group_name(k): v for k, v in class_vars.items()}


def class_traverse(cache, pyfile_name):
    """
    Recursive function for traversing class config hierarchies.
    """
    branch = cache
    for key, value in branch.items():
        if isinstance(value, type) and value.__module__ == pyfile_name:
            branch[key] = class_traverse(inherited_class_as_dict(value), pyfile_name)
    return branch


def directory_file_traverse(default_folder):
    """
    Traverse directories and Python file configs starting from directory.
    """
    cache = {}
    for dirpath, dirnames, filenames in os.walk(default_folder):
        if "__pycache__" in dirpath:
            continue

        path = dirpath.split("/")
        path_len = len(path)
        file_dict = {k[:-3]: class_traverse(
                                            module_as_dict(
                                                        import_module(dirpath.replace("/", ".") + "." + k[:-3])
                                                        ), 
                                            dirpath.replace("/", ".") + "." + k[:-3])
                     for k in filenames if k.endswith(".py")}
        branch = cache
        for index, directory in enumerate(path):
            branch = branch.setdefault(directory, file_dict if index == path_len - 1 else {})

    return cache
