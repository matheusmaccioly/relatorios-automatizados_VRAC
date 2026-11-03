SELECT txid_current_snapshot()::text AS snapshot,
       current_setting('transaction_isolation') AS isolation;
