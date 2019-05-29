from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Mapping

from .definitions import PythonType, DatastoreType
from .exceptions import UnknownSavedQueryError


@dataclass
class MappingDefinition:
    attr_name: str
    attr_type: PythonType
    field_name: str
    field_type: DatastoreType
    nullable: bool


@dataclass
class Constraint:
    type: str
    field_names: Iterable[str]
    extras: Optional[str]


@dataclass
class SavedQuery:
    name: str
    query: Any
    auto_mapping: bool


@dataclass
class ClassSpecification:
    name: str
    mappings: Iterable[MappingDefinition]
    id_fields: Iterable[str]
    defaults: Dict[str, Any]
    constraints: Iterable[Constraint]
    extras: Mapping[str, Any]
    saved_queries: Iterable[SavedQuery]

    def get_attribute_to_field_map(self) -> Dict[str, str]:
        return {
            m.attr_name: m.field_name
            for m in self.mappings
        }

    def get_field_to_attribute_map(self) -> Dict[str, str]:
        return {
            m.field_name: m.attr_name
            for m in self.mappings
        }

    def get_nullable_field_names(self) -> Iterable[str]:
        return [
            m.attr_name
            for m in self.mappings
            if m.nullable
        ]

    def saved_query(self, name: str) -> SavedQuery:
        for saved_query in self.saved_queries:
            if name == saved_query.name:
                return saved_query
        raise UnknownSavedQueryError(name)