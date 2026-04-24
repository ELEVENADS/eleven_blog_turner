"""
数据库模型定义
"""
from sqlalchemy import Column, String, Boolean, DateTime, create_engine, Integer, Text, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid
from eleven_blog_tunner.core.config import get_settings

Base = declarative_base()
settings = get_settings()

# 创建数据库引擎
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)


def get_db():
    """获取数据库会话（生成器版本，用于 FastAPI）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """获取数据库会话（直接返回版本，用于 Celery 任务）"""
    return SessionLocal()


class NoteCategory(Base):
    """笔记分类模型"""
    __tablename__ = "note_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    parent_id = Column(UUID(as_uuid=True), index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), default="all")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Note(Base):
    """笔记模型"""
    __tablename__ = "notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source_type = Column(String(20), nullable=False)
    file_path = Column(String(500))
    file_size = Column(Integer)
    word_count = Column(Integer, default=0)
    embedding_id = Column(String(100))
    is_vectorized = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)


class Article(Base):
    """文章模型"""
    __tablename__ = "articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), index=True)
    style_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    outline = Column(JSON)
    content = Column(Text)
    source_topic = Column(String(500))
    status = Column(String(20), default="draft")
    quality_score = Column(Float)
    fluency_score = Column(Float)
    originality_score = Column(Float)
    style_match_score = Column(Float)
    completeness_score = Column(Float)
    readability_score = Column(Float)
    word_count = Column(Integer, default=0)
    version = Column(Integer, default=1)
    parent_id = Column(UUID(as_uuid=True), index=True)
    review_id = Column(UUID(as_uuid=True), index=True)
    published_platform = Column(String(50))
    published_url = Column(String(500))
    meta_data = Column("metadata", JSON)  # 存储额外元数据，如错误信息、任务ID等
    celery_task_id = Column(String(100))  # Celery 任务ID
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    deleted_at = Column(DateTime)


class ArticleVersion(Base):
    """文章版本模型"""
    __tablename__ = "article_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    article_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    outline = Column(JSON)
    content = Column(Text, nullable=False)
    change_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)
