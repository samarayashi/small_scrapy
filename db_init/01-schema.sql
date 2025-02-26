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