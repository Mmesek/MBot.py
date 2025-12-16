CREATE OR REPLACE FUNCTION "modifyExp" ("user_id" bigint, "server_id" bigint, "value" double precision) RETURNS double precision LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "User" ("id") VALUES (user_id) ON CONFLICT DO NOTHING;
    value := value * SELECT COALESCE(
        SELECT "User"."exp_rate" 
        FROM "User" 
        WHERE 
        "User"."id" = "user_id"), 
        1.0);

    IF NOT EXISTS(
            SELECT "User_Experience"."timestamp" 
            FROM "User_Experience" 
            WHERE "User_Experience"."server_id" = "modifyExp".server_id 
            AND "User_Experience"."user_id" = "modifyExp".user_id) THEN
        INSERT INTO "User_Experience" ("server_id", "user_id", "type", "value") 
        VALUES ("modifyExp".server_id, "modifyExp".user_id, 0, "modifyExp".value);
    ELSIF NOW() - (
        SELECT "User_Experience"."timestamp" 
        FROM "User_Experience" 
        WHERE "User_Experience"."server_id" = "modifyExp".server_id 
        AND "User_Experience"."user_id" = "modifyExp".user_id
    ) >= make_interval(mins => 1) THEN
        UPDATE "User_Experience" 
        SET "value" = "User_Experience"."value" + "modifyExp".value, "timestamp" = now()
        WHERE "User_Experience"."server_id" = "modifyExp".server_id 
        AND "User_Experience"."user_id" = "modifyExp".user_id;
    END IF;
    RETURN 
        (SELECT "User_Experience"."value" 
        FROM "User_Experience" 
        WHERE "User_Experience"."server_id" = "modifyExp".server_id 
        AND "User_Experience"."user_id" = "modifyExp".user_id);
END$$
