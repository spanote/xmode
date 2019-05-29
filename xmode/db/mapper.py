from typing import Any, Iterable, Dict, Optional, Type
from .analyzer import spec
from .definitions import DateTime


class Mapper:
    @staticmethod
    def create_pyobj(cls: Type, data_from_datastore: Dict[str, Any]):
        s = spec(cls)
        f2a_map = s.get_field_to_attribute_map()
        field_type_map = {
            m.field_name: m.field_type
            for m in s.mappings
        }
        return cls(**{
            f2a_map[f]: Mapper._transform_from_field_value_to_attribute_value(field_type_map[f], v)
            for f, v in data_from_datastore.items()
        })

    @staticmethod
    def export_to_dict(obj, excluded: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        s = spec(type(obj))
        return {
            m.attr_name: getattr(obj, m.attr_name)
            for m in s.mappings
            if (not excluded or m.attr_name not in excluded)
        }

    @staticmethod
    def _transform_from_field_value_to_attribute_value(field_type, field_value):
        if field_value is None:
            return None
        if field_type == DateTime:
            # SQLAlchemy has already handled the type conversion.
            return field_value
        return field_type.__supertype__(field_value)

    @staticmethod
    def _transform_from_attribute_value_to_field_value(field_type, field_value):
        if field_value is None:
            return None
        if field_type == DateTime:
            # SQLAlchemy has already handled the type conversion.
            return field_value
        return field_type.__supertype__(field_value)


class MappingError(ValueError):
    pass
