-- 創建新聞分類表，將 category_key 當作主鍵
CREATE TABLE IF NOT EXISTS news_categories (
    category_key VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

-- 創建新聞文章表 (關聯新聞分類)，使用 news_category_key 作為外鍵
CREATE TABLE IF NOT EXISTS news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    publish_time TIMESTAMP NOT NULL,
    source VARCHAR(100) NOT NULL,
    news_category_key VARCHAR(50) NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- 為了LLM後續處理添加的欄位
    keywords TEXT[],
    summary TEXT,
    sentiment FLOAT,
    CONSTRAINT uk_news_title_url UNIQUE (title, url),
    FOREIGN KEY (news_category_key) REFERENCES news_categories(category_key)
);

-- 創建使用者表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    line_user_id VARCHAR(100) NOT NULL UNIQUE,
    is_registered BOOLEAN DEFAULT FALSE,
    registration_date TIMESTAMP,
    last_active TIMESTAMP
);

-- 創建天氣訂閱表
CREATE TABLE IF NOT EXISTS sub_weather (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    location_name VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 創建新聞訂閱表，使用 news_category_key 代替 news_category_id
CREATE TABLE IF NOT EXISTS sub_news (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    news_category_key VARCHAR(50) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (news_category_key) REFERENCES news_categories(category_key) ON DELETE CASCADE,
    CONSTRAINT uq_user_news_category UNIQUE (user_id, news_category_key)
);

-- 創建更新時間觸發器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_news_articles_updated_at
    BEFORE UPDATE ON news_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 初始化資料
-- 插入新聞分類資料 (依據 categories.json)
INSERT INTO news_categories (category_key, category_name) VALUES 
    ('4677', '台美半導體'),
    ('aall', '即時'),
    ('aipl', '政治'),
    ('aopl', '國際'),
    ('acn', '兩岸'),
    ('aie', '產經'),
    ('asc', '證券'),
    ('ait', '科技'),
    ('ahel', '生活'),
    ('asoc', '社會'),
    ('aloc', '地方'),
    ('acul', '文化'),
    ('aspt', '運動'),
    ('amov', '娛樂'),
    ('video', '影音'),
    ('newstopic', '專題'),
    ('4374', '媒體識讀');

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
