-- ELEVEN Blog Tuner 数据库建表语句
-- PostgreSQL 15+
-- 生成时间: 2026-04-17

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- ============================================
-- 2. 笔记分类表 (note_categories)
-- ============================================
CREATE TABLE note_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES note_categories(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_note_categories_user_id ON note_categories(user_id);
CREATE INDEX idx_note_categories_parent_id ON note_categories(parent_id);

-- 给 note_categories 添加 type 字段
ALTER TABLE note_categories ADD COLUMN type VARCHAR(20) DEFAULT 'all';

-- ============================================
-- 3. 标签表 (tags)
-- ============================================
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    color VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name, user_id)
);

CREATE INDEX idx_tags_user_id ON tags(user_id);

-- ============================================
-- 4. 笔记表 (notes)
-- ============================================
CREATE TABLE notes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES note_categories(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    source_type VARCHAR(20) NOT NULL,
    file_path VARCHAR(500),
    file_size INTEGER,
    word_count INTEGER DEFAULT 0,
    embedding_id VARCHAR(100),
    is_vectorized BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_notes_user_id ON notes(user_id);
CREATE INDEX idx_notes_category_id ON notes(category_id);
CREATE INDEX idx_notes_status ON notes(status);
CREATE INDEX idx_notes_created_at ON notes(created_at);

-- ============================================
-- 5. 笔记标签关联表 (note_tag_mapping)
-- ============================================
CREATE TABLE note_tag_mapping (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    note_id UUID NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(note_id, tag_id)
);

CREATE INDEX idx_note_tag_note_id ON note_tag_mapping(note_id);
CREATE INDEX idx_note_tag_tag_id ON note_tag_mapping(tag_id);

-- ============================================
-- 6. 风格表 (styles)
-- ============================================
CREATE TABLE styles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    style_vector JSONB,
    vocabulary_features JSONB,
    sentence_features JSONB,
    structure_features JSONB,
    writing_habits JSONB,
    sample_note_ids JSONB,
    sample_count INTEGER DEFAULT 0,
    confidence_score FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_styles_user_id ON styles(user_id);
CREATE INDEX idx_styles_is_active ON styles(is_active);

-- ============================================
-- 7. 风格特征表 (style_features)
-- ============================================
CREATE TABLE style_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    style_id UUID NOT NULL REFERENCES styles(id) ON DELETE CASCADE,
    feature_type VARCHAR(30) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value JSONB NOT NULL,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_style_features_style_id ON style_features(style_id);
CREATE INDEX idx_style_features_type ON style_features(feature_type);

-- ============================================
-- 8. 文章表 (articles)
-- ============================================
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    style_id UUID NOT NULL REFERENCES styles(id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    outline JSONB,
    content TEXT,
    source_topic VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft',
    quality_score FLOAT,
    fluency_score FLOAT,
    originality_score FLOAT,
    style_match_score FLOAT,
    completeness_score FLOAT,
    readability_score FLOAT,
    word_count INTEGER DEFAULT 0,
    version INTEGER DEFAULT 1,
    parent_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    review_id UUID,
    published_platform VARCHAR(50),
    published_url VARCHAR(500),
    metadata JSONB,  -- 存储额外元数据，如错误信息、任务ID等
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,
    deleted_at TIMESTAMP,
    category_id UUID REFERENCES note_categories(id) ON DELETE SET NULL
);

-- 给 articles 添加 category_id 字段
ALTER TABLE articles ADD COLUMN category_id UUID REFERENCES note_categories(id);

CREATE INDEX idx_articles_user_id ON articles(user_id);
CREATE INDEX idx_articles_style_id ON articles(style_id);
CREATE INDEX idx_articles_status ON articles(status);
CREATE INDEX idx_articles_parent_id ON articles(parent_id);
CREATE INDEX idx_articles_created_at ON articles(created_at);

-- ============================================
-- 9. 文章版本表 (article_versions)
-- ============================================
CREATE TABLE article_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    outline JSONB,
    content TEXT NOT NULL,
    change_summary TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(article_id, version)
);

CREATE INDEX idx_article_versions_article_id ON article_versions(article_id);

-- ============================================
-- 10. 文章大纲表 (article_outlines)
-- ============================================
CREATE TABLE article_outlines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    parent_section_id UUID,
    level INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL,
    word_count_target INTEGER,
    actual_word_count INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_article_outlines_article_id ON article_outlines(article_id);
CREATE INDEX idx_article_outlines_parent_section_id ON article_outlines(parent_section_id);

-- ============================================
-- 11. 审核记录表 (reviews)
-- ============================================
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    reviewer_type VARCHAR(20) NOT NULL,
    reviewer_id UUID,
    status VARCHAR(20) NOT NULL,
    quality_score FLOAT,
    fluency_score FLOAT,
    originality_score FLOAT,
    style_match_score FLOAT,
    completeness_score FLOAT,
    readability_score FLOAT,
    violation_flags JSONB,
    violation_details JSONB,
    suggestions TEXT,
    review_comments TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reviews_article_id ON reviews(article_id);
CREATE INDEX idx_reviews_status ON reviews(status);
CREATE INDEX idx_reviews_reviewer_type ON reviews(reviewer_type);

-- 添加外键到 articles.review_id
ALTER TABLE articles
ADD CONSTRAINT fk_articles_review_id
FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE SET NULL;

-- ============================================
-- 12. 发布记录表 (publications)
-- ============================================
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    platform_article_id VARCHAR(100),
    published_url VARCHAR(500),
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    published_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_publications_article_id ON publications(article_id);
CREATE INDEX idx_publications_platform ON publications(platform);
CREATE INDEX idx_publications_status ON publications(status);

-- ============================================
-- 13. 任务表 (tasks)
-- ============================================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    task_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    input_params JSONB NOT NULL,
    result JSONB,
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    error_code VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    estimated_duration INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_task_type ON tasks(task_type);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- ============================================
-- 14. 知识库表 (knowledge_base)
-- ============================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(20) NOT NULL,
    source_id UUID,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    metadata JSONB,
    chunk_index INTEGER DEFAULT 0,
    total_chunks INTEGER DEFAULT 1,
    vector_id VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_knowledge_user_id ON knowledge_base(user_id);
CREATE INDEX idx_knowledge_source_type ON knowledge_base(source_type);
CREATE INDEX idx_knowledge_content_hash ON knowledge_base(content_hash);
CREATE INDEX idx_knowledge_vector_id ON knowledge_base(vector_id);
CREATE INDEX idx_knowledge_is_active ON knowledge_base(is_active);

-- ============================================
-- 15. 系统配置表 (system_configs)
-- ============================================
CREATE TABLE system_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    value_type VARCHAR(20) DEFAULT 'string',
    description VARCHAR(500),
    config_group VARCHAR(50) DEFAULT 'default',
    is_encrypted BOOLEAN DEFAULT false,
    is_system BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_system_configs_key ON system_configs(config_key);
CREATE INDEX idx_system_configs_group ON system_configs(config_group);

-- ============================================
-- 初始化默认配置数据
-- ============================================
INSERT INTO system_configs (config_key, config_value, value_type, description, config_group, is_system) VALUES
-- LLM 配置
('llm.provider', 'openai', 'string', 'LLM提供商', 'llm', true),
('llm.model', 'gpt-4o', 'string', '默认模型', 'llm', true),
('llm.temperature', '0.7', 'number', '生成温度', 'llm', true),
('llm.max_tokens', '4096', 'number', '最大Token数', 'llm', true),
-- RAG 配置
('embedding.model', 'sentence-transformers/all-MiniLM-L6-v2', 'string', 'Embedding模型', 'rag', true),
('rag.chunk_size', '512', 'number', '分块大小', 'rag', true),
('rag.chunk_overlap', '50', 'number', '分块重叠', 'rag', true),
('rag.top_k', '5', 'number', '检索TopK', 'rag', true),
('rag.similarity_threshold', '0.7', 'number', '相似度阈值', 'rag', true),
-- 文章配置
('article.min_quality_score', '60', 'number', '文章最低质量分', 'article', true),
-- 发布配置
('publish.default_platform', 'notion', 'string', '默认发布平台', 'publish', true);

-- ============================================
-- 创建更新时间戳触发器函数
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要自动更新 updated_at 的表创建触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_note_categories_updated_at BEFORE UPDATE ON note_categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notes_updated_at BEFORE UPDATE ON notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_styles_updated_at BEFORE UPDATE ON styles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_article_outlines_updated_at BEFORE UPDATE ON article_outlines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publications_updated_at BEFORE UPDATE ON publications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configs_updated_at BEFORE UPDATE ON system_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
