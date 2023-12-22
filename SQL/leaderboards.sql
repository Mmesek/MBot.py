CREATE OR REPLACE FUNCTION get_leaderboard
    (
        server_id BIGINT,
        instance_id BIGINT,
        after TIMESTAMPTZ DEFAULT now() - interval '32d',
        before TIMESTAMPTZ DEFAULT now(),
        limit_at INT DEFAULT 100,
        user_id BIGINT DEFAULT NULL
    )
RETURNS TABLE (user_id BIGINT, quantity REAL)
AS
$$
SELECT
    "Transaction_Inventory".user_id,
    sum("Transaction_Inventory".quantity) as quantity
FROM
    "Transaction_Inventory"
LEFT JOIN
    "Transaction" ON
    "Transaction".id = "Transaction_Inventory".id
WHERE
    "Transaction".timestamp BETWEEN get_leaderboard.after AND get_leaderboard.before
    AND "Transaction_Inventory".item_id = get_leaderboard.instance_id
GROUP BY
    user_id,
    item_id
ORDER BY quantity DESC
LIMIT get_leaderboard.limit_at
;
$$
LANGUAGE sql;
