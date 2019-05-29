from typing import Any, Dict, Iterable, Iterator, Optional, Type, Union

from ..logger_factory import LoggerFactory

from .analyzer import spec
from .core import Core
from .mapper import Mapper

logger = LoggerFactory.get(__name__)


class DOA:
    def __init__(self, db: Core):
        self.__db = db

    @property
    def db(self):
        return self.__db

    def create(self, cls: Type = None, attributes: Dict[str, Any] = None, entity=None, return_nothing: bool = True):
        """
        Create a new entry
        """
        # Handle an entity (data model)
        if entity is not None:
            s = spec(type(entity))
            attributes = Mapper.export_to_dict(entity)
        elif cls is not None:
            s = spec(cls)

            for attr_name, default_value in s.defaults.items():
                if attr_name in attributes:
                    continue
                attributes[attr_name] = default_value() if callable(default_value) else default_value

            for field_name in s.get_nullable_field_names():
                if field_name in attributes:
                    continue
                attributes[field_name] = None

            entity = cls(**attributes)
        else:
            raise CreationError('The pattern of method invocation is not supported.')

        # Map to DB fields
        a2f_map = s.get_attribute_to_field_map()
        field_value_map = {
            a2f_map[a]: v
            for a, v in attributes.items()
        }
        field_list = field_value_map.keys()

        # Execute the query
        self.db.run(f'INSERT INTO {s.name}'
                    f' (`{"`, `".join(field_list)}`)'
                    f' VALUE ({", ".join([f":{f}" for f in field_list])})',
                    field_value_map)

        if return_nothing:
            return None

        return entity

    def save(self, entity, saved_attributes: Optional[Iterable[str]] = None):
        """
        Save the changes on the entity
        """
        s = spec(type(entity))
        attributes = Mapper.export_to_dict(entity)

        logger.debug('save: attributes = %s', attributes)

        # Map to DB fields
        a2f_map = s.get_attribute_to_field_map()

        logger.debug('save: a2f_map = %s', a2f_map)

        field_value_map = {
            a2f_map[a]: v
            for a, v in attributes.items()
            if not saved_attributes or a in saved_attributes
        }

        logger.debug('save: field_value_map = %s', field_value_map)

        identifiers = {
            a2f_map[a]: getattr(entity, a)
            for a in s.id_fields
        }

        set_clauses = [
            f'`{k}` = :updated_{k}'
            for k in field_value_map.keys()
        ]

        where_clauses = [
            f'`{k}` = :current_{k}'
            for k in identifiers.keys()
        ]

        if not set_clauses:
            raise NoUpdateError(entity)

        params = {}
        params.update({f'current_{k}': v for k, v in identifiers.items()})
        params.update({f'updated_{k}': v for k, v in field_value_map.items()})

        update_query = f'UPDATE {s.name} SET {", ".join(set_clauses)} WHERE {" AND ".join(where_clauses)}'

        # Execute the query
        self.db.run(update_query, params)

    def find(self,
             cls: Type,
             where_clause: Optional[str] = None,
             params: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
        s = spec(cls)
        query = f'SELECT * FROM {s.name}'

        if where_clause is not None:
            query += f' WHERE {where_clause}'

        rows = self.db.run_and_return(query, params)

        if len(rows) == 0:
            return iter([])

        return self._finalize_result(cls, rows, auto_mapping=True)

    def play(self, cls: Type, saved_query_name: str, params: Optional[Dict[str, Any]] = None) -> Iterator[Any]:
        s = spec(cls)
        saved_query = s.saved_query(saved_query_name)
        query = saved_query.query
        rows = self.db.run_and_return(query, params)

        if len(rows) == 0:
            return iter(list())

        return self._finalize_result(cls, rows, auto_mapping=saved_query.auto_mapping)

    def refresh(self, entity):
        s = spec(type(entity))
        a2f_map = s.get_attribute_to_field_map()
        # f2a_map = s.get_field_to_attribute_map()

        identifiers = {
            a2f_map[a]: getattr(entity, a)
            for a in s.id_fields
        }

        where_clauses = [
            f'`{k}` = :{k}'
            for k in identifiers.keys()
        ]

        query = f'SELECT * FROM {s.name} WHERE {" AND ".join(where_clauses)}'
        result = self.db.run_and_return(query, identifiers)

        if not result:
            raise EntityRemovedError(entity)

        updates = result[0]

        for a, f in a2f_map.items():
            setattr(entity, a, updates[f])

    @staticmethod
    def _finalize_result(cls: Type, rows: Iterator[Any], auto_mapping: bool):
        for row in rows:
            yield Mapper.create_pyobj(cls, dict(row)) if auto_mapping else dict(row)


class CreationError(RuntimeError):
    pass


class NoUpdateError(RuntimeError):
    pass


class EntityRemovedError(RuntimeError):
    pass
