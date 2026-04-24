# ELEVEN Blog Tuner

## 项目基础信息

- **项目名**：ELEVEN Blog Tuner
- **项目目的**：个人博客 AI 智能助手，根据个人笔记学习并生成相似文笔的文章
- **项目创建日期**：2026/4/15
- **项目作者**：ELEVEN(elven)

## 项目功能描述

### 核心功能
1. **风格学习**：从个人笔记中学习写作风格和特点
2. **文章生成**：根据学习到的风格生成新的文章
3. **文章发布**：支持将生成的文章发布到多种博客平台

### 系统功能架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层 (Vue3)                         │
├─────────────────────────────────────────────────────────────────┤
│                      OpenAPI 服务层 (FastAPI)                    │
├─────────────────────────────────────────────────────────────────┤
│                      Gateway 层 (控制系统核心)                    │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ TaskManager │ APIHandler  │StatusMonitor │ Integration  │  │
│  │   任务管理器   │   API处理器   │   状态监控    │   集成模块    │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  用户管理  │  笔记管理  │  风格学习  │  文章生成  │  文章发布  │ 系统配置 │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
```

### 核心 Agent 说明

系统包含 5 个核心 AI Agent，通过协作完成文章生成任务：

| Agent | 职责 | 核心功能 |
|-------|------|---------|
| **Boss Agent** | 统筹系统任务调度和信息返回 | 接收用户请求、协调其他Agent工作流程、汇总执行结果 |
| **System Agent** | 系统内任务状态查询和参数返回 | 获取用户风格配置数据、获取系统运行参数、查询任务执行状态 |
| **Summary Agent** | 总结类工作 | 上下文压缩与总结、文章风格特征提取、长文本摘要生成、多文档融合总结 |
| **Writer Agent** | 文章撰写 | 根据主题和风格撰写文章、按照大纲逐段生成、支持局部重写和润色 |
| **Review Agent** | 审查文章质量和是否违规 | 内容质量评分、敏感词和违规检测、生成修改建议、提供优化方向 |
| **Assistant Agent** | 辅助写作 | 文本续写、风格提取、内容改写、润色优化、写作建议、内容扩写与总结 |

### 核心流程说明

#### 文章生成流程

```
用户输入 → Boss Agent (任务调度) → System Agent (获取风格配置) → Summary Agent (分析上下文) → RAG Pipeline (检索相关知识) → Writer Agent (撰写文章) → Review Agent (质量审查) → 输出文章
```

#### RAG 处理流程

```
原始文档 → Document Washer (清洗) → Chunker (分块) → Embedding Service (向量化) → Vector DB (存储)

查询时: 查询文本 → Embedding (向量化) → Searcher (向量检索 Top-K*2) → Reranker (精排 Top-K) → 返回结果
```

#### Gateway 层工作流程

```
接收请求 → 任务创建 → BossAgent调度 → Agent执行 → 状态监控 → 结果返回
```

### 技术特点
- **多 LLM 提供商支持**：集成 OpenAI 和本地 Ollama 模型
- **Agent 协作**：5 个核心 Agent 协同工作，实现复杂任务处理
- **RAG 增强**：检索增强生成，提高文章质量和相关性
- **记忆系统**：短期和长期记忆，保持对话上下文

## 技术栈

- **后端**：Python 3.10+, FastAPI
- **前端**：Vue3, Vite, TypeScript
- **AI 模型**：OpenAI API, Ollama 本地模型
- **向量数据库**：Chroma (计划中)
- **任务队列**：Celery (计划中)
- **缓存**：Redis (计划中)

## 项目结构

项目采用清晰的分层架构，确保职责分离：

```
eleven_blog_tunner/
├── __init__.py              # 包初始化，版本信息
├── main.py                  # FastAPI 应用入口
│
├── core/                    # 核心层 - 基础设施
│   ├── __init__.py
│   ├── config.py            # 统一配置管理 (pydantic-settings)
│   ├── exceptions.py        # 自定义异常类
│   ├── cache.py             # 缓存模块
│   └── connection_pool.py   # 连接池管理
│
├── agents/                  # Agent 层 - AI 智能体
│   ├── __init__.py
│   ├── base_agent.py        # Agent 抽象基类
│   ├── agent_protocol.py    # Agent 通信协议（集成熔断机制）
│   ├── boss_agent.py        # Boss Agent (任务调度)
│   ├── system_agent.py      # System Agent (系统查询)
│   ├── summary_agent.py     # Summary Agent (总结逻辑)
│   ├── writer_agent.py      # Writer Agent (文章撰写)
│   ├── review_agent.py      # Review Agent (内容审查)
│   └── assistant_agent.py   # Assistant Agent (辅助写作)
│
├── rag/                     # RAG 层 - 检索增强生成
│   ├── __init__.py
│   ├── document_washer.py   # 文档清洗
│   ├── chunker.py           # 文档分块
│   ├── embedding.py         # 向量化服务
│   ├── searcher.py          # 向量检索
│   ├── reranker.py          # 结果重排序
│   ├── pipeline.py          # RAG 处理管道
│   ├── note_importer.py     # 笔记导入
│   ├── style_learner.py     # 风格学习
│   ├── style_manager.py     # 风格管理
│   └── vector_db_optimize.py # 向量数据库优化
│
├── llm/                     # LLM 层 - 大语言模型
│   ├── __init__.py
│   ├── base.py              # LLM 抽象基类
│   ├── openai_provider.py   # OpenAI 提供商实现
│   ├── local_provider.py    # 本地 Ollama 提供商实现
│   ├── factory.py           # LLM 工厂
│   └── memory.py            # 记忆管理
│
├── tools/                   # Tools 层 - 工具集
│   ├── __init__.py
│   ├── mcp_tools.py         # MCP 工具集管理
│   └── skill_manager.py     # Skill 管理器
│
├── api/                     # API 层 - HTTP 接口
│   ├── __init__.py
│   └── routes/              # 路由定义
│
├── utils/                   # 工具层 - 通用工具
│   ├── __init__.py
│   └── logger.py            # 日志系统 (loguru)
│
└── common/                  # Common 层 - 公共工具
    └── __init__.py
```

### 架构设计原则

1. **分层架构**：API 层、Gateway 层、Core 层、Agent 层、RAG 层、LLM 层、Tools 层
2. **模块化设计**：每个模块独立负责特定功能，模块间通过接口通信
3. **可扩展性**：支持多 LLM 提供商、插件化工具注册机制、可插拔的 RAG 组件
4. **异常处理体系**：分层异常、标准化错误响应、详细错误信息、可追踪性

## 安装说明

### 开发环境

1. **克隆项目**
   ```bash
   git clone https://github.com/ELEVENADS/eleven_blog_turner.git
   cd ELEVEN_BLOG_TUNNER
   ```

2. **安装依赖**
   ```bash
   python3 -m pip install -e .
   ```

3. **配置环境变量**
   创建 `.env` 文件，配置以下参数：
   ```env
   # API 配置
   API_KEY=your_openai_api_key
   
   # LLM 配置
   LLM_PROVIDER=openai  # 或 local
   LLM_MODEL=gpt-4
   LLM_TEMPERATURE=0.7
   LLM_MAX_TOKENS=4096
   
   # 本地 LLM 配置
   LOCAL_LLM_BASE_URL=http://localhost:11434/api
   LOCAL_LLM_MODEL=qwen3.5:9b
   
   # RAG 配置
   VECTOR_DB_PATH=./data/vector_db
   EMBEDDING_MODEL=text-embedding-3-small
   CHUNK_SIZE=1000
   
   # 数据库
   DATABASE_URL=sqlite:///./data/app.db
   
   # 日志
   LOG_LEVEL=INFO
   ```

4. **运行开发服务器**
   ```bash
   python3 run.py
   ```

### 生产环境

使用 Gunicorn + Uvicorn Workers 部署：

```bash
gunicorn eleven_blog_tunner.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 开发进度

### 已完成
- ✅ 基础架构搭建
- ✅ 统一配置管理 (pydantic-settings)
- ✅ 异常处理体系
- ✅ 日志系统集成 (loguru)
- ✅ 数据库模型设计
- ✅ 单元测试框架
- ✅ OpenAI 提供商实现
- ✅ 本地 Ollama 提供商实现
- ✅ LLM 工厂模式优化
- ✅ 向量数据库 (Chroma)
- ✅ RAG Pipeline (清洗→分块→向量化→检索→重排)
- ✅ 文档处理 (Markdown/TXT/PDF)
- ✅ Embedding 服务
- ✅ 向量检索与重排序
- ✅ Agent 熔断机制
- ✅ 缓存模块
- ✅ 连接池管理
- ✅ Agent 间通信协议
- ✅ 前端界面 (Vue3)
- ✅ 用户认证和权限管理 (JWT + bcrypt)
- ✅ Gateway 层任务调度
- ✅ 风格学习与风格管理
- ✅ 记忆系统实现

### 待完成
- [ ] 实现文章发布功能 (对接博客平台)
- [ ] 测试与部署

## 使用方法

### LLM 模块使用

```python
from eleven_blog_tunner.llm.factory import LLMFactory

# 创建 LLM 实例
llm = LLMFactory.create(provider="openai")

# 发送对话
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"}
]

response = await llm.chat(messages)
print(response)

# 流式对话
async for chunk in llm.stream_chat(messages):
    print(chunk, end="")
```

### 测试 LLM 提供商

```bash
# 测试所有提供商
python3 -m eleven_blog_tunner.llm.factory

# 测试指定提供商
python3 -m eleven_blog_tunner.llm.factory local qwen3.5:9b
```

## 扩展指南

### 添加新的 LLM 提供商
1. 在 `llm/` 下创建新的 provider 文件
2. 继承 `BaseLLM` 实现 `chat()` 和 `stream_chat()`
3. 在 `factory.py` 的 `_providers` 中注册

### 添加新的 Agent
1. 在 `agents/` 下创建新的 agent 文件
2. 继承 `BaseAgent` 实现 `execute()`
3. 在 `AgentProtocol._init_builtin_agents()` 中注册

### 添加新的 Tool
1. 在 Agent 的 `_init_tools()` 方法中使用 `add_tool()` 注册
2. 实现具体的工具逻辑
3. 通过 `call_tool()` 调用

## 贡献指南

1. **提交规范**
   - `feat`: 新功能
   - `fix`: 修复 bug
   - `docs`: 文档更新
   - `style`: 代码格式调整
   - `refactor`: 重构
   - `test`: 测试相关
   - `chore`: 构建/工具相关

2. **代码风格**
   - 使用 Black 格式化 (line-length: 100)
   - 使用 Ruff 进行代码检查
   - 类型注解必须完整
   - 文档字符串使用双引号

## 许可证

MIT License

## 联系方式

- 作者：ELEVEN(elven)
- 项目地址：[项目仓库地址](https://github.com/ELEVENADS/eleven_blog_turner)
