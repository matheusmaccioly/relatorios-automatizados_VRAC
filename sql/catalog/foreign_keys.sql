-- Apenas relações declaradas cuja origem E destino pertencem ao escopo aprovado.
-- Ausência de linhas não prova ausência de relacionamentos.
SELECT TOP (:row_limit)
    ss.name AS source_schema,
    so.name AS source_table,
    sc.name AS source_column,
    fk.name AS constraint_name,
    fkc.constraint_column_id AS column_ordinal,
    ts.name AS target_schema,
    tob.name AS target_table,
    tc.name AS target_column,
    fk.is_disabled AS is_disabled,
    fk.is_not_trusted AS is_not_trusted
FROM sys.foreign_keys AS fk
INNER JOIN sys.foreign_key_columns AS fkc ON fkc.constraint_object_id = fk.object_id
INNER JOIN sys.objects AS so ON so.object_id = fkc.parent_object_id
INNER JOIN sys.schemas AS ss ON ss.schema_id = so.schema_id
INNER JOIN sys.columns AS sc
    ON sc.object_id = so.object_id AND sc.column_id = fkc.parent_column_id
INNER JOIN sys.objects AS tob ON tob.object_id = fkc.referenced_object_id
INNER JOIN sys.schemas AS ts ON ts.schema_id = tob.schema_id
INNER JOIN sys.columns AS tc
    ON tc.object_id = tob.object_id AND tc.column_id = fkc.referenced_column_id
WHERE ss.name = :schema
    AND ss.name IN :allowed_schemas
    AND ts.name IN :allowed_schemas
    AND so.type = 'U'
    AND tob.type = 'U'
    AND so.is_ms_shipped = 0
    AND tob.is_ms_shipped = 0
ORDER BY ss.name, so.name, so.object_id, fk.name, fk.object_id, fkc.constraint_column_id;
