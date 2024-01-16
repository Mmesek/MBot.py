CREATE OR REPLACE FUNCTION "attackBoss" ("user_id" bigint, "server_id" bigint, "gladiator_id" integer, "boss_id" integer, "damage" integer, "bonus" integer) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO "Gladiator" ("guild_id", "user_id") VALUES (server_id, user_id) ON CONFLICT DO NOTHING;
    IF (
        SELECT "Gladiator_Boss"."health"
        FROM "Gladiator_Boss"
        WHERE "Gladiator_Boss".id = gladiator_id
    ) > 0 THEN
        UPDATE "Gladiator_Boss"
        SET "health" = "Gladiator_Boss"."health" - (damage + bonus)
        WHERE "Gladiator_Boss".id = gladiator_id;

        INSERT INTO "Gladiator_History" ("user_id", "guild_id", "gladiator_id", "boss_id", "damage", "bonus")
        VALUES (user_id, server_id, gladiator_id, boss_id, damage, bonus) ON CONFLICT DO NOTHING;
    END IF;
END$$
