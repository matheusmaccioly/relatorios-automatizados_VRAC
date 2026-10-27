-- Somente chaves PK/UQ declaradas; uma linha por coluna da chave.
SELECT TOP (:row_limit)
    s.name AS schema_name,
    o.name AS object_name,
    kc.name AS constraint_name,
    kc.type AS constraint_type,
    c.name AS column_name,
    ic.key_ordinal AS key_ordinal
FROM sys.key_constraints AS kc
INNER JOIN sys.objects AS o ON o.object_id = kc.parent_object_id
INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
INNER JOIN sys.index_columns AS ic
    ON ic.object_id = o.object_id AND ic.index_id = kc.unique_index_id
INNER JOIN sys.columns AS c
    ON c.object_id = ic.object_id AND c.column_id = ic.column_id
WHERE s.name = :schema
    AND o.type = 'U'
    AND o.is_ms_shipped = 0
    AND kc.type IN ('PK', 'UQ')
    AND ic.key_ordinal > 0
ORDER BY s.name, o.name, o.object_id, kc.name, kc.object_id, ic.key_ordinal;
