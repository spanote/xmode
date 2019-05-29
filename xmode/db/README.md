# xmode.db

This is an experimental DOA using SQLAlchemy and Data Class. The main goal of this module is to simplify data-related operations.

## Define a model (table)

To define the structure of the data to store in the database, we use the generic `@dataclass` (from `dataclasses`) with a few extra decorators.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import uuid4

from xmode.db.definitions import UUID, Boolean, DateTime, Integer, String
from xmode.db.analyzer import constraint, default, identified_by, save_query, stored_in


@stored_in('profiles')
@identified_by('id')  # This is a PK.
@constraint('index', ('approved',))
@default('id', lambda: str(uuid4()))
@default('approved', False)
@default('created_at', datetime.utcnow)
@dataclass
class Profile:
    id: UUID  # In MySQL, this field is a string.
    name: String
    age: Optional[Integer]  # In MySQL, this field is NULLABLE.
    approved: Boolean  # In MySQL, this field is TINYINT.
    created_at: DateTime
```

* `@stored_in('profiles')` means the data will be stored in the table called `profiles`. This is optional and by default, the SQL generator will use the name of the class as the name of the table.
* `@identified_by('id')` means `id` is the PK of this table. You can make a compound PK by adding more than one fields, e.g., `@identified_by('col_1', 'col_2', ..., 'col_n')`.
* `@constraint(type: str, fields: Iterable[str])` means to create a constrain of `type` (e.g., `index`, `unique`) with the given `fields`.
* `@default(field: str, value_or_callback: Union[Any, Callable])` means to define the static default value or the function to generate the default value dynamically. *Please note that by default, the generated schema (in SQL) will not define the default value and the value will be applicable on write operation by DOA.

## Generate the table schema

You will need to use the combination of both `sqlalchemy` and `xmode.db`

```python
from sqlalchemy import create_engine

from xmode.db.sql_generator import MySQL

with create_engine('mysql://db/app').connect() as c:
    c.execute(MySQL.convert_class_to_create_query(Profile))
```

## Create a new entry

First, create a DOA object.

```python
from xmode.db.core import Core
from xmode.db.doa import DOA

db = Core('mysql://db', 'app')
doa = DOA(db)
```

### From an object directly

```python
p1 = Profile(id=str(uuid4()), name='Foo', age=25, approved=True, created_at=datetime.utcnow())

new_p = doa.create(entity=p1, return_nothing=False)
```

`new_p` and `p1` is the same object.

### Via DOA

```python
p2 = doa.create(Profile, dict(name='Bar'))
```

`p2` is `Profile(id='...', name='Bar', age=None, approved=False, created_at=datetime(...))`.

## Find objects

```python
profiles = doa.find(Profile, 'approved = :approved', dict(approved=True))
```

`profiles` is a generator of Profile and in this case, it only returns p1.

## Update an object

```python
p2.approved = True
doa.save(p2)
```

This is to update `p2` with current (mapped) properties.

To specify which properties to save, you can do it by:

```python
doa.save(p2, saved_attributes=['approved'])
```

## To refresh objects

At some point the objects might be out of date, you can refresh them by using `DOA.refresh`.

```python
doa.refresh(p1)
```

At this point, `p1` is refreshed.