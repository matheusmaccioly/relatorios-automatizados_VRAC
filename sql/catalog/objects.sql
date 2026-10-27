-- Catálogo restrito ao schema aprovado; somente metadados de tabelas e views.
SELECT TOP (:row_limit)
    s.name AS schema_name,
    o.name AS object_name,
    CASE WHEN o.type = 'U' THEN 'table' ELSE 'view' END AS object_type
FROM sys.objects AS o
INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
WHERE s.name = :schema
    AND o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
ORDER BY s.name, o.name, o.object_id;
