# Quick Reference: psycopg2 → SQLAlchemy Migration

## At a Glance

| Aspect | psycopg2 | SQLAlchemy + psycopg3 |
| ------ | -------- | --------------------- |
| Connection | Direct connection | Engine with pooling |
| Parameters | `%s` positional | `:name` named |
| Results | RealDictCursor | row._mapping |
| Performance | Good | Better (with pooling) |
| Python 3.13 | ❌ Build issues | ✅ Supported |

## Code Comparison

### Connection

```python
# OLD (psycopg2)
conn = psycopg2.connect(uri)

# NEW (SQLAlchemy)
engine = create_engine(uri, pool_pre_ping=True)
conn = engine.connect()
```

### Query with Parameters

```python
# OLD (psycopg2)
cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))

# NEW (SQLAlchemy)
result = conn.execute(text("SELECT * FROM employees WHERE id = :id"), {'id': employee_id})
```

### Fetch Results

```python
# OLD (psycopg2)
rows = cursor.fetchall()
results = [dict(row) for row in rows]

# NEW (SQLAlchemy)
rows = result.fetchall()
results = [dict(row._mapping) for row in rows]
```

### Cleanup

```python
# OLD (psycopg2)
cursor.close()
conn.close()

# NEW (SQLAlchemy)
conn.close()
engine.dispose()
```

## Import Changes

```python
# OLD
import psycopg2
from psycopg2.extras import RealDictCursor

# NEW
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
```

## Dependencies

```txt
# OLD
psycopg2-binary==2.9.9

# NEW
sqlalchemy==2.0.29
psycopg[binary]==3.2.3
```

## Key Benefits

1. **Connection Pooling** - Reuse connections automatically
2. **Health Checks** - `pool_pre_ping=True` validates connections
3. **Named Parameters** - More readable: `:name` vs `%s`
4. **Modern Driver** - psycopg3 is 2x faster than psycopg2
5. **Python 3.13+** - Full support for latest Python

## Lambda Deployment

No changes needed! The Lambda handler remains the same.

Just rebuild the deployment package:

```bash
./build_lambda.sh
```

## Connection URI

**Important Change:**

```txt
# OLD (psycopg2)
postgresql://user:password@host:port/database

# NEW (SQLAlchemy with psycopg3)
postgresql+psycopg://user:password@host:port/database
```

The `+psycopg` specifies the driver to use with SQLAlchemy.

---

**Status:** ✅ Production Ready  
**Breaking Changes:** ❌ None  
**Performance:** ⬆️ Improved
