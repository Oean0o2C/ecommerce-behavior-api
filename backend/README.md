# Backend

FastAPI 后端服务代码目录，提供 RESTful API 接口供前端调用。

## 技术栈

- **Python**: 3.11+
- **FastAPI**: 0.110+ - 现代、高性能的 Web 框架
- **SQLAlchemy**: 2.0+ - ORM 框架，使用同步驱动
- **psycopg**: 3.x - PostgreSQL 数据库驱动
- **Pydantic**: 2.0+ - 数据验证与序列化
- **Uvicorn**: ASGI 服务器

## 项目结构

```
backend/
├── app/                    # 业务代码
│   ├── api/               # API 路由层
│   │   ├── __init__.py
│   │   ├── category.py    # 品类分析接口
│   │   ├── products.py    # 商品分析接口
│   │   ├── sales.py       # 销售分析接口
│   │   └── user.py        # 用户分析接口
│   ├── models/            # 数据模型层
│   │   ├── __init__.py
│   │   └── models.py      # SQLAlchemy ORM 模型
│   ├── repositories/      # 数据访问层
│   │   ├── __init__.py
│   │   ├── category_repository.py
│   │   ├── products_repository.py
│   │   ├── sales_repository.py
│   │   └── user_repository.py
│   ├── services/          # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── category_service.py
│   │   ├── products_service.py
│   │   ├── sales_service.py
│   │   └── user_service.py
│   ├── __init__.py
│   ├── database.py        # 数据库连接配置
│   ├── init_db.py         # 数据库初始化脚本
│   └── main.py            # FastAPI 应用入口
├── tests/                 # 测试代码
│   └── test_api.py
├── Procfile               # Railway 部署配置
├── requirements.txt       # 依赖包列表
└── start.py               # 本地启动脚本
```

## 架构设计

采用分层架构设计，职责分离清晰：

```
┌─────────────────────────────────────────┐
│           API Routers (api/)            │
│  - 路径定义、参数校验、依赖注入           │
├─────────────────────────────────────────┤
│           API Services (services/)      │
│  - 业务逻辑编排、数据聚合、缓存策略       │
├─────────────────────────────────────────┤
│          Repository Layer (repositories/)│
│  - 数据库访问、ORM 查询、原生 SQL        │
├─────────────────────────────────────────┤
│          Models (models/)               │
│  - 数据模型定义、表结构映射              │
├─────────────────────────────────────────┤
│          Database (PostgreSQL)          │
│  - 连接池管理、事务控制、查询优化         │
└─────────────────────────────────────────┘
```

## 本地开发

### 环境要求

- Python 3.11+
- PostgreSQL 数据库（推荐使用 Supabase）

### 进入虚拟环境

**Windows:**
```bash
# 进入项目根目录
cd d:\Cources\@za\项目1

# 激活虚拟环境
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
# 进入项目根目录
cd /path/to/项目1

# 激活虚拟环境
source .venv/bin/activate
```

激活成功后，命令行提示符前会显示 `(.venv)`。

### 安装依赖

**所有依赖已在项目根目录的 `requirements.txt` 中统一管理。**

```bash
# 确保已在虚拟环境中，然后在项目根目录安装依赖
cd d:\Cources\@za\项目1
pip install -r requirements.txt
```

**注意**：不需要单独安装 backend 依赖，根目录的 `requirements.txt` 已包含所有前后端依赖。

### 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DATABASE_URL=postgresql+psycopg://username:password@host:port/database?sslmode=require
```

**注意**：使用 Supabase 时，建议使用 Session pooler 连接串（端口 5432）。

### 启动服务

**重要：确保已激活虚拟环境（见上文），然后进入 backend 目录启动服务：**

```bash
# 进入 backend 目录
cd backend

# 方式1：使用启动脚本
python start.py

# 方式2：直接使用 uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## API 接口列表

| 方法 | 路径 | 描述 | 参数 |
|------|------|------|------|
| GET | /health | 健康检查 | - |
| GET | /api/v1/sales/overview | 销售概览 | start_date, end_date |
| GET | /api/v1/sales/trend | 销售趋势 | granularity, start_date, end_date |
| GET | /api/v1/category/performance | 品类表现 | category_level, limit |
| GET | /api/v1/user/funnel | 用户漏斗 | start_date, end_date |
| GET | /api/v1/user/rfm | RFM 分层 | segment |
| GET | /api/v1/products/top | 热销商品 | metric, limit |

## 数据库设计

采用星型模型（Star Schema）设计：

- **维度表**：dim_users, dim_products, dim_time
- **事实表**：fact_user_behavior
- **物化视图**：mv_daily_sales, mv_category_stats, mv_user_rfm

详细表结构见 `docs/sql/schema.sql`。

## 测试

```bash
# 运行测试
pytest tests/
```

## 生产部署

**生产环境**托管在 **Railway**（与根目录 `README.md` 部署架构一致）。

### Railway 部署步骤

1. 在 Railway 创建新项目
2. 连接 GitHub 仓库
3. 配置环境变量 `DATABASE_URL`
4. 部署自动触发

详细部署指南见 `docs/deployment_guide.md`。

## 性能优化

- 使用数据库连接池
- 物化视图预聚合常用查询
- 合理的索引策略
- 分页查询大数据集

详细优化策略见 `docs/performance_optimization.md`。

## 注意事项

1. **数据库驱动**：项目使用同步驱动 `psycopg`，而非 `asyncpg`
2. **连接池**：SQLAlchemy 自动管理连接池，无需手动配置
3. **错误处理**：所有接口返回统一的响应格式，包含 code、data、message、timestamp
4. **CORS**：已配置允许跨域访问，支持前端调用

## 相关文档

- [环境配置指南](../docs/environment_setup.md)
- [部署指南](../docs/deployment_guide.md)
- [性能优化](../docs/performance_optimization.md)
- [项目决策记录](../docs/project_decisions_and_issues.md)
