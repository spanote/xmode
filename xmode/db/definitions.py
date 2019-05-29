from datetime import datetime
from typing import NewType, TypeVar


PythonType = TypeVar('PythonType')
UUID = NewType('UUID', str)
String = NewType('String', str)
Boolean = NewType('Boolean', bool)
Integer = NewType('Integer', int)
Text = NewType('Text', str)
DateTime = NewType('DateTime', datetime)
DatastoreType = TypeVar('DatastoreType', UUID, String, Boolean, Integer, Text)
