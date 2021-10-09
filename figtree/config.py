from figtree.extract import *

__all__ = ["config"]

class Config(dict):
    def __init__(self):
        self.default_folder = "configs"

    def __call__(self, config_path = None, reset = True):
        if config_path == None:
            config_path = self.default_folder

        config_path = config_path.replace("\\", "/").replace(".", "/")

        if config_path[-1] == "/":
            config_path = config_path[:-1]

        is_dir, partial_dir = is_path_dir(config_path)
        is_py, py_file = is_path_py(config_path, partial_dir)
        is_class, classes = is_path_class(config_path, partial_dir, py_file, reset = reset)

        if is_dir:
            self.update(directory_file_traverse(config_path))

        if is_py or is_class:
            pyfile_name = partial_dir.replace("/", ".") + "." + py_file
            self.update(class_traverse(classes, pyfile_name))

config = Config()