from re import compile
from typing import Any, Dict, Iterable, Optional, Union

from .definitions import UUID, Boolean, DateTime, Integer, String, Text
from .spec_model import ClassSpecification, Constraint, MappingDefinition, SavedQuery


def spec(cls) -> ClassSpecification:
    """
    Get the model specification
    :param cls: Dataclass class
    :return: Class specification
    """
    return Analyzer.analyze_annotation(cls)


def stored_in(storage_name):
    def decorator(cls):
        s = spec(cls)
        s.name = storage_name

        return cls
    return decorator


def identified_by(*attr_names):
    def decorator(cls):
        s = spec(cls)
        s.id_fields = sorted(set(s.id_fields + list(attr_names)))

        return cls
    return decorator


def constraint(type: Optional[str], field_names: Union[str, Iterable[str]], extras: Optional[str] = None):
    def decorator(cls):
        s = spec(cls)
        s.constraints.append(Constraint(type=type,
                                        field_names=[field_names] if isinstance(field_names, str) else field_names,
                                        extras=extras))

        return cls
    return decorator


def default(attr_name: str, value: Any):
    def decorator(cls):
        s = spec(cls)
        s.defaults[attr_name] = value

        return cls
    return decorator


def save_query(name: str, query: str, auto_mapping: bool = True):
    def decorator(cls):
        s = spec(cls)
        s.saved_queries.append(SavedQuery(name=name, query=query, auto_mapping=auto_mapping))

        return cls
    return decorator


class Analyzer:
    __metadata_prop_name__ = '__x_schema__'
    __re_typing_name__ = compile(r'^typing\.(?P<kind>.+)\[.+\]$')

    @staticmethod
    def analyze_annotation(cls):
        metadata_prop_name = Analyzer.__metadata_prop_name__

        if hasattr(cls, metadata_prop_name):
            return getattr(cls, metadata_prop_name)

        class_spec = ClassSpecification(name=cls.__name__.lower(),
                                        mappings=[],
                                        id_fields=[],
                                        defaults={},
                                        constraints=[],
                                        extras={},
                                        saved_queries=[])

        setattr(cls, metadata_prop_name, class_spec)

        class_spec = spec(cls)
        class_spec.mappings = [
            Analyzer._analyze_mapping(k, v)
            for k, v in cls.__annotations__.items()
            if k[0] != '_'
        ]

        return class_spec

    @staticmethod
    def _analyze_mapping(attr_name: str, annotation: Any) -> MappingDefinition:
        common_info = dict(attr_name=attr_name,
                           attr_type=annotation,
                           field_name=attr_name,
                           nullable=False)
        common_info.update(Analyzer._convert_to_field_type(annotation))
        return MappingDefinition(**common_info)

    @staticmethod
    def _convert_to_field_type(annotation) -> Dict[str, Union[str, bool]]:
        # Predefined Types
        if annotation in [UUID, Boolean, DateTime, Integer, String, Text]:
            return dict(field_type=annotation)

        # Built-in Types
        string_repr_type = str(annotation)
        matches = Analyzer.__re_typing_name__.search(string_repr_type)

        if not matches:
            raise NonConvertableAnnotationError(annotation.__name__, annotation)

        kind = matches.groupdict()['kind']

        if kind == 'Union':
            if type(None) not in annotation.__args__:
                raise ForbiddenDynamicTypeError(annotation)
            for template_annotation in annotation.__args__:
                if template_annotation == type(None):
                    continue
                template_spec = Analyzer._convert_to_field_type(template_annotation)
                break

            template_spec['nullable'] = True

            return template_spec

        raise NonConvertableAnnotationError(annotation.__name__, annotation)


class NonConvertableAnnotationError(TypeError):
    pass


class ForbiddenDynamicTypeError(TypeError):
    pass
