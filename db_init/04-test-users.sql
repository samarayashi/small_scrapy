-- 使用單一 CTE 串聯所有插入操作
WITH inserted_user AS (
    -- 插入使用者資料並返回 ID
    INSERT INTO users (user_name, line_user_id, is_registered, registration_date, last_active)
    VALUES ('FarEastern hospital', 'U85bfd24c5c8d48b0c9e3ed09d9791f97', TRUE, NOW(), NOW())
    RETURNING id
), inserted_weather AS (
    -- 插入天氣訂閱資料
    INSERT INTO sub_weather (user_id, longitude, latitude, location_name)
    SELECT id, 121.45289859534898, 24.999037728346977, '亞東醫院'
    FROM inserted_user
)
-- 插入新聞訂閱資料
INSERT INTO sub_news (user_id, news_category_key)
SELECT inserted_user.id, c.category_key
FROM inserted_user
CROSS JOIN (
    VALUES 
        ('acul'),  -- 文化
        ('aie'),   -- 產經
        ('ait')    -- 科技
) AS c(category_key); 