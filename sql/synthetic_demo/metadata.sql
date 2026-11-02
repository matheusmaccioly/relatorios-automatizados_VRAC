-- Contrato genérico do banco exclusivamente sintético local.
SELECT m.synthetic, m.version, m.seed,
       current_database() AS database_name, current_user AS role_name,
       current_setting('transaction_read_only') AS transaction_read_only,
       s.ssl
FROM vrac_sintetico.dataset_metadata AS m
CROSS JOIN pg_catalog.pg_stat_ssl AS s
WHERE s.pid = pg_backend_pid();
