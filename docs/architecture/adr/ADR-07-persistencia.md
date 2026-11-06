# ADR-07. Persistencia: modelos ORM separados del dominio y Unit of Work

- **Estado:** Aceptado.
- **Contexto:** El dominio (DDD) no debe depender de SQLAlchemy (ADR-06). Cada caso de uso debe ser atómico: si falla, no queda ningún cambio parcial (DS-02).
- **Alternativas:** (a) mapear las clases del dominio directamente con SQLAlchemy (mapeo imperativo); (b) modelos ORM separados y repositorios que traducen; (c) SQL a mano.
- **Decisión:** (b). `src/infrastructure/models.py` define las tablas; `repositories.py` traduce fila ↔ agregado; `SqlAlchemyUnitOfWork` abre una transacción por caso de uso y hace rollback si no hubo `commit()`. Los puertos (`ports.py`) son la única dependencia de la capa de aplicación.
- **Detalles:** importes con `Decimal` exacto (`NUMERIC` en PostgreSQL, texto en SQLite); fechas en UTC con zona horaria; existencias con `SELECT ... FOR UPDATE` para que dos ventas simultáneas no descuenten el mismo stock; bitácora `historial` de sólo inserción (RF-16).
- **Consecuencias:** (+) el dominio queda puro y probado sin base de datos; (+) los mismos tests de aplicación corren contra memoria y contra SQL, lo que demuestra que ambos adaptadores cumplen el contrato; (−) hay que mantener la traducción fila ↔ agregado cuando cambia un agregado.
- **Trazabilidad:** RF-16 (auditoría), RN-07, DS-01, DS-02; `tests/integration/test_sql_persistencia.py`, `tests/conftest.py`.
