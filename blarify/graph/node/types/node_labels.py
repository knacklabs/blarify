from enum import Enum


class NodeLabels(Enum):
    FOLDER = "FOLDER"
    FILE = "FILE"
    FUNCTION = "FUNCTION"
    CLASS = "CLASS"
    ENUM = "ENUM"
    METHOD = "METHOD"
    MODULE = "MODULE"
    DELETED = "DELETED"
