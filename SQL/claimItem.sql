CREATE OR REPLACE FUNCTION "claimItem" 
    ("server_id" bigint, "user_ids" bigint[], "instance_id" INT, "quantity" double precision, 
    "required_instance_id" INT DEFAULT null, "required_quantity" double precision DEFAULT null,
    OUT "users" bigint[]
    ) 
    RETURNS bigint[] LANGUAGE plpgsql AS $$
BEGIN
    -- For each user
    FOREACH user_id IN ARRAY user_ids
    LOOP
        -- Add user in case user is not in Database
        INSERT INTO "User" ("id") 
        VALUES (user_id) ON CONFLICT DO NOTHING;
        IF required_instance_id is not null AND (
            SELECT "quantity" 
            FROM "Inventory"
            WHERE "Inventory"."user_id" = user_id
            AND "Inventory"."instance_id" = required_instance_id
        ) < required_quantity THEN
            -- Check if user has required item, if so, check if user has less than required and skip
            CONTINUE;

        ELSIF required_instance_id is not null THEN
            -- User apparently has more than enough, deduce required quantity
            UPDATE "Inventory"
            SET quantity = "Inventory".quantity - required_quantity
            WHERE "Inventory".user_id = user_id
            AND "Inventory".instance_id = required_instance_id;
        END IF;

        INSERT INTO "Inventory" (user_id, instance_id, quantity) 
        VALUES (user_id, instance_id, quantity) 
        ON CONFLICT ON CONSTRAINT "Inventory_pkey" DO 
            UPDATE "Inventory" 
            SET quantity = "Inventory".quantity + quantity
            WHERE "Inventory".user_id = user_id
            AND "Inventory".instance_id = instance_id;
        -- Add claimed item, or increase existing
        
        users := array_append(users, user_id);
        -- Append array with users that received item
    END LOOP;
RETURN users;
-- Return array of users that received item
END$$
