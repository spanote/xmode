from abc import ABC, abstractmethod

from .analyzer import spec
from .spec_model import ClassSpecification
from .definitions import UUID, Boolean, DateTime, Integer, String, Text,LongText


class SqlGenerator(ABC):
    @staticmethod
    @abstractmethod
    def convert_class_to_create_query(cls) -> str:
        ...

    @staticmethod
    @abstractmethod
    def generate_create_query(s: ClassSpecification) -> str:
        ...


class MySQL(SqlGenerator):
    @staticmethod
    def convert_class_to_create_query(cls) -> str:
        class_spec = spec(cls)
        return MySQL.generate_create_query(class_spec)

    @staticmethod
    def generate_create_query(s: ClassSpecification) -> str:
        field_type_to_db_type_map = {
            UUID: 'VARCHAR(36)',
            Boolean: 'TINYINT(1)',
            DateTime: 'DATETIME',
            Integer: 'INTEGER(11)',
            String: 'VARCHAR(255)',
            Text: 'TEXT',
		    LongText: 'LONGTEXT'
        }

        definitions = []

        for md in s.mappings:
            db_type = field_type_to_db_type_map[md.field_type]
            definitions.append(f'`{md.field_name}` {db_type} {"NULL DEFAULT NULL" if md.nullable else "NOT NULL"}')

        definitions.append(f'PRIMARY KEY (`{"`, `".join(s.id_fields)}`)')

        for c in s.constraints:
            definitions.append(f'{c.type.upper()} (`{"`, `".join(c.field_names)}`) {c.extras or ""}'.strip())

        return f'CREATE TABLE {s.name} ({", ".join(definitions)})'
