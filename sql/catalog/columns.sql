-- max_length é expresso em bytes; -1 representa um tipo de comprimento máximo.
-- Nomes de tipos personalizados fora dos schemas aprovados ficam ocultos.
SELECT TOP (:row_limit)
    s.name AS schema_name,
    o.name AS object_name,
    c.name AS column_name,
    c.column_id AS column_ordinal,
    CASE
        WHEN dt.is_user_defined = 0 OR ts.name IN :allowed_schemas THEN dt.name
        ELSE NULL
    END AS data_type,
    CASE
        WHEN dt.is_user_defined = 0 OR ts.name IN :allowed_schemas THEN ts.name
        ELSE NULL
    END AS data_type_schema,
    bt.name AS base_data_type,
    c.max_length AS max_length_bytes,
    c.precision AS numeric_precision,
    c.scale AS numeric_scale,
    c.is_nullable AS is_nullable,
    c.is_identity AS is_identity
FROM sys.objects AS o
INNER JOIN sys.schemas AS s ON s.schema_id = o.schema_id
INNER JOIN sys.columns AS c ON c.object_id = o.object_id
LEFT JOIN sys.types AS dt ON dt.user_type_id = c.user_type_id
LEFT JOIN sys.schemas AS ts ON ts.schema_id = dt.schema_id
LEFT JOIN sys.types AS bt
    ON bt.user_type_id = c.system_type_id AND bt.is_user_defined = 0
WHERE s.name = :schema
    AND o.type IN ('U', 'V')
    AND o.is_ms_shipped = 0
ORDER BY s.name, o.name, o.object_id, c.column_id;
