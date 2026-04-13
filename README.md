# 电商用户行为数据分析平台

## 需求说明书与架构设计

**版本**：v1.0\
**日期**：2026-04-02

***

## 快捷文档入口

- 环境配置与本地运行：[docs/environment\_setup.md](docs/environment_setup.md)
- 项目关键决策与问题复盘：[docs/project\_decisions\_and\_issues.md](docs/project_decisions_and_issues.md)
- **部署约定**：后端 **Railway**（FastAPI），前端 **Streamlit Cloud**（Streamlit），数据库 **Supabase**。生产库在 Supabase 中**完整执行** `docs/sql/` 脚本顺序见 [docs/README.md](docs/README.md)。

## 快速开始

### 1. 环境准备

- Python 3.11+
- 虚拟环境（推荐）

### 2. 安装依赖

```bash
# 创建并激活虚拟环境
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# 安装所有依赖（前后端统一）
pip install -r requirements.txt
```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件：

```env
DATABASE_URL=postgresql+psycopg://username:password@host:port/database?sslmode=require
```

### 4. 启动服务

**启动后端（终端1）：**
```bash
# 确保在虚拟环境中
cd backend
python start.py
```
后端服务运行在 http://localhost:8000

**启动前端（终端2）：**
```bash
# 确保在虚拟环境中
cd frontend
streamlit run app.py
```
前端应用运行在 http://localhost:8501

详细说明见 [backend/README.md](backend/README.md) 和 [frontend/README.md](frontend/README.md)。

### 5. 已部署环境

**生产环境：**
- **后端 API**：https://ecommerce-behavior-api-production.up.railway.app
- **前端应用**：https://ecommerce-behavior-api-ymkretx2b4fq3zpobkzyjm.streamlit.app/

**API 文档：**
- https://ecommerce-behavior-api-production.up.railway.app/docs

***

## 项目结构

```
backend/      # FastAPI 服务
  app/        # 业务代码
    api/      # API 路由
    models/   # 数据模型
    repositories/ # 数据访问层
    services/ # 业务逻辑层
    database.py # 数据库连接配置
    init_db.py # 数据库初始化
    main.py   # FastAPI 应用入口
  tests/      # 后端测试
  Procfile    # Railway 部署配置
  requirements.txt # 后端依赖（部署到 Railway）
  start.py    # 启动脚本
  README.md   # 后端说明文档
etl/          # ETL 脚本与 Notebook
  README.md
  etl_pipeline.py
  kaggle_etl.ipynb
  local_import.py
frontend/     # Streamlit 应用
  app.py      # 前端主应用
  requirements.txt # 前端依赖（部署到 Streamlit Cloud）
  README.md   # 前端说明文档
scripts/      # 运维与辅助脚本
docs/         # 设计与使用文档
  README.md
  environment_setup.md
  project_decisions_and_issues.md
  sql/
    dim_time_seed.sql  # 备用生成 dim_time（与 ETL 导入二选一）
    generated_columns_triggers.sql
    indexes_constraints.sql
    schema.sql
data/         # 数据落地目录（本地）
  raw/        # 原始数据
  processed/  # 清洗后数据
    kaggle_outputs/outputs/        # 或 outputs_7d_sample10/ 等抽样输出目录
```

***

## 数据流向概览

```mermaid
flowchart TD
  A[Kaggle 原始 CSV\n2019-Oct/Nov] --> B[分块读取与清洗\nnormalize_events/clean_events]
  B --> C[维度累积统计\nusers/products/time]
  B --> D[事实表分块暂存\nfact_user_behavior_*.parquet]
  C --> E[维表输出\n dim_time.parquet\n dim_users.parquet\n dim_products.parquet]
  D --> F[本地输出目录\noutputs/fact_user_behavior_parts/]
  E --> G[local_import.py\n维表导入]
  F --> H[local_import.py\n事实表导入]
  G --> I[(Supabase/PostgreSQL)]
  H --> I
```

***

## 第一章 项目概述

### 1.1 项目背景

本项目基于 Kaggle 电商用户行为数据集（eCommerce behavior data from multi category store），构建完整的数据工程链路，实现从原始数据清洗到可视化展示的端到端数据平台。项目对标企业级数据仓库建设要求，覆盖离线数据处理、维度建模、API 服务化、前端可视化等核心环节。

### 1.2 项目目标

| 目标层级     | 具体描述                                              |
| -------- | ------------------------------------------------- |
| **功能目标** | 构建可在线访问的电商数据分析平台，支持用户行为漏斗分析、实时销售看板、用户画像查询         |
| **技术目标** | 掌握云原生数据架构，实践现代数据工程工具链（Supabase/FastAPI/Streamlit） |
| **职业目标** | 产出可演示的作品集，支撑大数据研发工程师岗位面试                          |

### 1.3 项目范围

**包含范围**：

- 千万级原始数据的清洗与转换（ETL）
- 维度建模与数据仓库构建
- RESTful API 设计与实现
- 交互式数据可视化
- 云基础设施部署与运维

**不包含范围**：

- 实时流处理（预留扩展接口，项目二实现）
- 机器学习模型（项目三扩展）
- 用户权限与支付系统

***

## 第二章 需求分析

### 2.1 功能需求

#### 2.1.1 数据接入层（Kaggle Notebook）

| 需求编号    | 需求描述                                     | 优先级 |
| ------- | ---------------------------------------- | --- |
| ETL-001 | 支持从 Kaggle Dataset 流式读取 CSV（分块处理，避免内存溢出） | P0  |
| ETL-002 | 实现数据清洗（空值处理、异常值过滤、格式标准化）                 | P0  |
| ETL-003 | 实现数据转换（时间维度拆解、类目层级解析、价格归一化）              | P0  |
| ETL-004 | 支持清洗后数据批量写入云数据库（批量插入，事务控制）               | P0  |
| ETL-005 | 提供数据质量检查报告（记录数校验、字段空值率、重复值检测）            | P1  |

#### 2.1.2 数据存储层（Supabase PostgreSQL）

| 需求编号   | 需求描述                                         | 优先级 |
| ------ | -------------------------------------------- | --- |
| DB-001 | 设计星型模型（事实表 + 维度表），支持 OLAP 查询                 | P0  |
| DB-002 | 实现用户维度表（dim\_users），包含用户注册信息、地域、设备类型         | P0  |
| DB-003 | 实现商品维度表（dim\_products），包含类目层级、品牌、价格区间        | P0  |
| DB-004 | 实现时间维度表（dim\_time），支持年/季/月/周/日/小时多级钻取        | P0  |
| DB-005 | 实现用户行为事实表（fact\_user\_behavior），记录事件类型、时间、金额 | P0  |
| DB-006 | 创建物化视图（mv\_sales\_summary），预聚合日/周/月销售指标      | P1  |
| DB-007 | 配置行级安全策略（RLS），实现数据访问控制                       | P2  |

#### 2.1.3 API 服务层（FastAPI）

| 需求编号    | 需求描述                                              | 优先级 |
| ------- | ------------------------------------------------- | --- |
| API-001 | 提供健康检查接口（/health），返回服务状态与数据库连接状态                  | P0  |
| API-002 | 提供销售概览接口（/api/v1/sales/overview），返回 GMV、订单数、客单价   | P0  |
| API-003 | 提供趋势分析接口（/api/v1/sales/trend），支持按时间粒度（日/周/月）查询    | P0  |
| API-004 | 提供品类分析接口（/api/v1/category/performance），返回各品类销售额占比 | P0  |
| API-005 | 提供用户行为漏斗接口（/api/v1/user/funnel），返回浏览→加购→购买转化率     | P0  |
| API-006 | 提供用户画像接口（/api/v1/user/profile），返回 RFM 分层结果        | P1  |
| API-007 | 支持分页查询、时间范围过滤、字段筛选                                | P1  |
| API-008 | 自动生成 OpenAPI 文档（Swagger UI），支持在线调试                | P0  |

#### 2.1.4 可视化层（Streamlit）

| 需求编号   | 需求描述                      | 优先级 |
| ------ | ------------------------- | --- |
| UI-001 | 展示销售总览仪表盘（KPI 卡片 + 趋势折线图） | P0  |
| UI-002 | 展示品类分析图表（饼图/柱状图/树图）       | P0  |
| UI-003 | 展示用户行为漏斗图（漏斗图 + 转化率标注）    | P0  |
| UI-004 | 支持时间范围选择器（最近7天/30天/自定义）   | P0  |
| UI-005 | 支持数据下钻（从品类点击看商品明细）        | P1  |
| UI-006 | 支持数据导出（CSV/Excel 下载）      | P1  |

### 2.2 非功能需求

| 类别       | 需求描述     | 指标                          |
| -------- | -------- | --------------------------- |
| **性能**   | API 响应时间 | 95% 请求 < 200ms              |
| **性能**   | 数据库查询时间  | 简单查询 < 100ms，聚合查询 < 500ms   |
| **可用性**  | 服务可用性    | 演示期间 99%（允许维护窗口）            |
| **可扩展性** | 架构预留     | 支持后续接入 Kafka/Flink 实时流      |
| **安全性**  | 数据传输     | 全链路 HTTPS，数据库 SSL 强制        |
| **可维护性** | 代码规范     | 类型注解覆盖率 > 80%，单元测试覆盖率 > 60% |

### 2.3 数据需求

#### 2.3.1 数据源说明

| 属性   | 描述                                                                |
| ---- | ----------------------------------------------------------------- |
| 来源   | Kaggle Dataset: eCommerce behavior data from multi category store |
| 规模   | 2019-Oct.csv (5.3GB, 4200万条) + 2019-Nov.csv (9GB, 6700万条)         |
| 格式   | CSV，含 9 个字段                                                       |
| 更新频率 | 静态数据集（一次性导入）                                                      |

#### 2.3.2 原始数据字段

| 字段名            | 类型        | 描述                             | 清洗规则                  |
| -------------- | --------- | ------------------------------ | --------------------- |
| event\_time    | TIMESTAMP | 事件时间戳                          | 解析为 UTC，拆分为日期/时间维度    |
| event\_type    | VARCHAR   | 事件类型（view/cart/purchase）       | 枚举值校验，异常值标记           |
| product\_id    | INTEGER   | 商品 ID                          | 空值过滤                  |
| category\_id   | BIGINT    | 类目 ID（层级编码）                    | 解析为 category\_code 层级 |
| category\_code | VARCHAR   | 类目路径（如 electronics.smartphone） | 拆分为一级/二级/三级类目         |
| brand          | VARCHAR   | 品牌名称                           | 空值填充为 "Unknown"       |
| price          | FLOAT     | 商品价格                           | 负值过滤，异常值截断            |
| user\_id       | INTEGER   | 用户 ID                          | 空值过滤                  |
| user\_session  | VARCHAR   | 会话 ID                          | 用于关联同一会话行为            |

***

## 第三章 系统架构设计

### 3.1 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户访问层                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Streamlit     │  │   Swagger UI    │  │  Supabase       │  │
│  │   (数据可视化)    │  │   (API 文档)    │  │  Studio         │  │
│  │                 │  │                 │  │  (数据管理)      │  │
│  │  • 销售仪表盘     │  │  • 接口调试      │  │  • 表结构查看    │  │
│  │  • 漏斗分析      │  │  • 参数验证      │  │  • SQL 编辑器    │  │
│  │  • 品类洞察      │  │  • 响应预览      │  │  • RLS / 权限    │ │
│  └────────┬────────┘  └─────────────────┘  └─────────────────┘ │
│           │                                                    │
│           └──────────────────┬─────────────────────────────────┘
│                              │ HTTPS
├──────────────────────────────┼───────────────────────────────────┤
│                         API 网关层 (Railway)                     │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Application                      │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │  │   Routers   │  │  Services   │  │   Repositories      │  │ │
│  │  │  (API 路由)  │  │  (业务逻辑)  │  │   (数据访问层)        │  │ │
│  │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │ │
│  │         └─────────────────┴────────────────────┘            │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │ │
│  │  │  Pydantic   │  │ SQLAlchemy  │  │  psycopg            │  │ │
│  │  │ (请求/响应)  │  │  (ORM 模型)  │  │  (同步驱动/连接池)     │  │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │ │
│  └──────────────────────────┬──────────────────────────────────┘ │
│                             │ SSL + Connection Pool              │
├─────────────────────────────┼────────────────────────────────────┤
│                      数据存储层 (Supabase)                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                  PostgreSQL（Supabase 托管）                 │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │  Dimension  │  │    Fact     │  │   Materialized      │ │ │
│  │  │   Tables    │  │   Tables    │  │      Views          │ │ │
│  │  │             │  │             │  │                     │ │ │
│  │  │ dim_users   │  │fact_user_   │  │ mv_daily_sales      │ │ │
│  │  │ dim_products│  │  behavior   │  │ mv_category_stats   │ │ │
│  │  │ dim_time    │  │             │  │ mv_user_rfm         │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据处理层 (Kaggle Notebook)                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Extract   │  │ Transform   │  │        Load             │  │
│  │             │  │             │  │                         │  │
│  │ • 分块读取   │  │ • 清洗规则   │  │ • 批量写入 (COPY/INSERT)  │  │
│  │ • 类型推断   │  │ • 维度建模   │  │ • 事务控制                │  │
│  │ • 进度监控   │  │ • 数据质量   │  │ • 索引创建                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │              Alembic (Schema 版本管理)                       │ │
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 数据架构设计

#### 3.2.1 维度模型设计（星型模型）

```
                    ┌─────────────────┐
                    │   dim_time      │
                    │  (时间维度)      │
                    │  ─────────────  │
                    │  time_key (PK)  │
                    │  date_actual    │
                    │  year           │
                    │  quarter        │
                    │  month          │
                    │  week           │
                    │  day_of_week    │
                    │  is_weekend     │
                    └────────┬────────┘
                             │
                             │
    ┌─────────────────┐      │      ┌─────────────────┐
    │   dim_users     │      │      │  dim_products   │
    │  (用户维度)      │      │      │  (商品维度)     │
    │  ─────────────  │      │      │  ─────────────  │
    │  user_key (PK)  │      │      │  product_key(PK)│
    │  user_id (NK)   │      │      │  product_id(NK) │
    │  first_seen     │      │      │  category_id    │
    │  last_seen      │      │      │  category_l1    │
    │  user_segment   │      │      │  category_l2    │
    │  region         │      │      │  category_l3    │
    │  device_type    │      │      │  brand          │
    └────────┬────────┘      │      │  price_range    │
             │               │      └────────┬────────┘
             │               │               │
             └───────────────┼───────────────┘
                             │
                    ┌────────┴──────────┐
                    │ fact_user_behavior│
                    │   (行为事实表)     │
                    │  ───────────────  │
                    │  event_id (PK)    │
                    │  time_key (FK)    │
                    │  user_id (FK)     │
                    │  product_id (FK)  │
                    │  event_type       │
                    │  price            │
                    │  quantity         │
                    │  revenue          │
                    └───────────────────┘
```

#### 3.2.2 表结构详细设计

**dim\_time（时间维度表）**

| 字段名           | 类型       | 约束            | 说明               |
| ------------- | -------- | ------------- | ---------------- |
| time\_key     | INTEGER  | PK            | 代理键（YYYYMMDD 格式） |
| date\_actual  | DATE     | NOT NULL      | 实际日期             |
| year          | SMALLINT | NOT NULL      | 年份               |
| quarter       | SMALLINT | NOT NULL      | 季度（1-4）          |
| month         | SMALLINT | NOT NULL      | 月份（1-12）         |
| week          | SMALLINT | NOT NULL      | 周数（1-52）         |
| day\_of\_week | SMALLINT | NOT NULL      | 星期几（0-6）         |
| is\_weekend   | BOOLEAN  | NOT NULL      | 是否周末             |
| is\_holiday   | BOOLEAN  | DEFAULT FALSE | 是否节假日            |

**dim\_users（用户维度表）**

| 字段名               | 类型          | 约束                | 说明                       |
| ----------------- | ----------- | ----------------- | ------------------------ |
| user\_key         | SERIAL      | PK                | 代理键                      |
| user\_id          | INTEGER     | UNIQUE, NOT NULL  | 自然键（原始 user\_id）         |
| first\_seen\_date | DATE        | NOT NULL          | 首次活跃日期                   |
| last\_seen\_date  | DATE        | NOT NULL          | 最后活跃日期                   |
| user\_segment     | VARCHAR(20) | DEFAULT 'new'     | 用户分层（new/active/churned） |
| region            | VARCHAR(50) | DEFAULT 'unknown' | 地域（需 IP 解析，暂用 unknown）   |
| device\_type      | VARCHAR(20) | DEFAULT 'desktop' | 设备类型（需解析 user\_agent）    |

**dim\_products（商品维度表）**

| 字段名          | 类型          | 约束                | 说明                  |
| ------------ | ----------- | ----------------- | ------------------- |
| product\_key | SERIAL      | PK                | 代理键                 |
| product\_id  | INTEGER     | UNIQUE, NOT NULL  | 自然键                 |
| category\_id | BIGINT      | NOT NULL          | 原始类目 ID             |
| category\_l1 | VARCHAR(50) | NOT NULL          | 一级类目（如 electronics） |
| category\_l2 | VARCHAR(50) | NOT NULL          | 二级类目（如 smartphone）  |
| category\_l3 | VARCHAR(50) | DEFAULT 'other'   | 三级类目                |
| brand        | VARCHAR(50) | DEFAULT 'Unknown' | 品牌                  |
| price\_range | VARCHAR(20) | GENERATED         | 价格区间（low/mid/high）  |

**fact\_user\_behavior（行为事实表）**

| 字段名           | 类型            | 约束                 | 说明                       |
| ------------- | ------------- | ------------------ | ------------------------ |
| event\_id     | BIGSERIAL     | PK                 | 自增主键                     |
| time\_key     | INTEGER       | FK → dim\_time     | 时间外键                     |
| user\_id      | INTEGER       | FK → dim\_users    | 用户自然键外键                  |
| product\_id   | INTEGER       | FK → dim\_products | 商品自然键外键                  |
| event\_type   | VARCHAR(20)   | NOT NULL           | 事件类型（view/cart/purchase） |
| price         | DECIMAL(10,2) | NOT NULL           | 当时商品价格                   |
| quantity      | SMALLINT      | DEFAULT 1          | 数量（purchase 时≥1）         |
| revenue       | DECIMAL(12,2) | GENERATED          | 计算字段（price \* quantity）  |
| user\_session | VARCHAR(50)   | NOT NULL           | 会话 ID（用于漏斗分析）            |

#### 3.2.3 物化视图设计

**mv\_daily\_sales（日销售汇总）**

```sql
-- 按日期聚合核心指标
SELECT 
    t.date_actual,
    COUNT(DISTINCT f.user_id) as uv,
    COUNT(*) as pv,
    COUNT(*) FILTER (WHERE f.event_type = 'purchase') as order_count,
    SUM(f.revenue) FILTER (WHERE f.event_type = 'purchase') as gmv,
    AVG(f.revenue) FILTER (WHERE f.event_type = 'purchase') as avg_order_value
FROM fact_user_behavior f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.date_actual;
```

**mv\_category\_stats（品类统计）**

```sql
-- 按类目聚合销售与浏览指标
SELECT 
    p.category_l1,
    p.category_l2,
    COUNT(*) as view_count,
    COUNT(*) FILTER (WHERE f.event_type = 'cart') as cart_count,
    COUNT(*) FILTER (WHERE f.event_type = 'purchase') as purchase_count,
    SUM(f.revenue) as gmv
FROM fact_user_behavior f
JOIN dim_products p ON f.product_id = p.product_id
GROUP BY p.category_l1, p.category_l2;
```

**mv\_user\_rfm（用户 RFM 分层）**

```sql
-- 计算用户 RFM 指标
WITH user_stats AS (
    SELECT 
        user_id,
        MAX(date_actual) as last_purchase_date,
        COUNT(*) FILTER (WHERE event_type = 'purchase') as frequency,
        SUM(revenue) FILTER (WHERE event_type = 'purchase') as monetary
    FROM fact_user_behavior f
    JOIN dim_time t ON f.time_key = t.time_key
    WHERE f.event_type = 'purchase'
    GROUP BY user_id
)
SELECT 
    user_id,
    CURRENT_DATE - last_purchase_date as recency,
    frequency,
    monetary,
    NTILE(5) OVER (ORDER BY CURRENT_DATE - last_purchase_date) as r_score,
    NTILE(5) OVER (ORDER BY frequency DESC) as f_score,
    NTILE(5) OVER (ORDER BY monetary DESC) as m_score
FROM user_stats;
```

### 3.3 API 架构设计

#### 3.3.1 接口清单

| 方法  | 路径                           | 描述     | 核心参数                                |
| --- | ---------------------------- | ------ | ----------------------------------- |
| GET | /health                      | 健康检查   | -                                   |
| GET | /api/v1/sales/overview       | 销售概览   | start\_date, end\_date              |
| GET | /api/v1/sales/trend          | 销售趋势   | granularity, start\_date, end\_date |
| GET | /api/v1/category/performance | 品类表现   | category\_level, limit              |
| GET | /api/v1/user/funnel          | 用户漏斗   | start\_date, end\_date              |
| GET | /api/v1/user/rfm             | RFM 分层 | segment                             |
| GET | /api/v1/products/top         | 热销商品   | metric, limit                       |

#### 3.3.2 响应规范

**成功响应（200 OK）**

```json
{
  "code": 200,
  "data": {
    "gmv": 1250000.50,
    "order_count": 3420,
    "uv": 15600,
    "conversion_rate": 0.0219
  },
  "message": "success",
  "timestamp": "2026-04-02T18:13:00Z"
}
```

**错误响应（4xx/5xx）**

```json
{
  "code": 422,
  "data": null,
  "message": "Invalid date format, expected YYYY-MM-DD",
  "timestamp": "2026-04-02T18:13:00Z"
}
```

#### 3.3.3 分层架构

```
┌─────────────────────────────────────────┐
│           API Routers                   │
│  (路径定义 + 参数校验 + 依赖注入)         │
├─────────────────────────────────────────┤
│           API Services                  │
│  (业务逻辑编排 + 数据聚合 + 缓存策略)      │
├─────────────────────────────────────────┤
│          Repository Layer               │
│  (数据库访问 + ORM 查询 + 原生 SQL)       │
├─────────────────────────────────────────┤
│          Database (PostgreSQL)        │
│  (连接池管理 + 事务控制 + 查询优化)        │
└─────────────────────────────────────────┘
```

### 3.4 部署架构设计

#### 3.4.1 环境划分

| 环境      | 用途   | 数据库                  | 后端              | 前端                   |
| ------- | ---- | -------------------- | --------------- | -------------------- |
| Dev     | 本地开发 | Supabase 项目（dev）     | localhost:8000  | localhost:8501       |
| Staging | 集成测试 | Supabase 项目（staging） | Railway dev 环境  | Streamlit Cloud dev  |
| Prod    | 生产演示 | Supabase 项目（prod）    | Railway prod 环境 | Streamlit Cloud prod |

生产及其它新建环境：在 Supabase **SQL Editor** 中按 [docs/README.md](docs/README.md) 顺序**完整执行** `docs/sql/`（含 **`schema.sql`** **中全部表与物化视图**），再执行触发器与索引脚本。

#### 3.4.2 CI/CD 流程

```
GitHub Push/PR
    │
    ▼
┌─────────────────┐
│  GitHub Actions  │
│  • 代码格式检查   │
│  • 单元测试       │
│  • 构建 Docker 镜像│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Railway 部署   │  (自动部署 main 分支)
│   • 拉取镜像     │
│   • 环境变量注入 │
│   • 健康检查     │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│  Streamlit Cloud │  (前端自动部署)
│  • 连接生产 API  │
└─────────────────┘
```

#### 3.4.3 成本估算（免费额度内）

| 服务              | 免费额度                                                                | 本项目用量                     | 是否超限                |
| --------------- | ------------------------------------------------------------------- | ------------------------- | ------------------- |
| Supabase        | [Pricing](https://supabase.com/pricing) 与 Dashboard **Database** 用量 | 本项目采用抽样子集（如 7 天 + 10% 用户） | 以 Dashboard 用量与配额为准 |
| Railway         | $5/月信用额度                                                            | \~$2/月（轻量服务）              | 否                   |
| Streamlit Cloud | 1 个公开应用                                                             | 1 个                       | 否                   |
| **总计**          | -                                                                   | **$0/月**                  | -                   |

***

## 第四章 技术选型说明

### 4.1 选型对比

| 组件   | 候选方案                             | 最终选择                | 理由                                       |
| ---- | -------------------------------- | ------------------- | ---------------------------------------- |
| 云数据库 | 各托管 PostgreSQL                   | **Supabase**        | 托管 PostgreSQL，自带 Studio 与 RLS，连接串标准、生态成熟 |
| ORM  | SQLAlchemy / Prisma / Django ORM | **SQLAlchemy 2.0**  | Python 生态标准，类型支持好，FastAPI 原生集成           |
| 后端框架 | FastAPI / Flask / Django         | **FastAPI**         | 异步性能优，自动生成文档，现代 Python 首选                |
| 前端框架 | Streamlit / React / Vue          | **Streamlit**       | 纯 Python 开发，数据场景组件丰富，部署简单                |
| 后端部署 | Railway / Render / Fly.io        | **Railway**         | GitHub 集成、日志与额度；承载 FastAPI               |
| 前端托管 | Streamlit Cloud 等                | **Streamlit Cloud** | 与 Streamlit 栈一致，公开应用托管                   |

### 4.2 技术栈版本

| 组件         | 版本                                                      | 说明          |
| ---------- | ------------------------------------------------------- | ----------- |
| Python     | 3.11+                                                   | 类型注解、性能优化   |
| FastAPI    | 0.110+                                                  | 依赖注入、中间件支持  |
| SQLAlchemy | 2.0+                                                    | 声明式模型、同步支持  |
| Pydantic   | 2.0+                                                    | 数据验证与序列化    |
| Streamlit  | 1.32+                                                   | 缓存机制、连接池优化  |
| PostgreSQL | 与 Supabase 项目一致（在 Dashboard **Settings → Database** 查看） | Supabase 托管 |

***

## 第五章 实施计划

### 5.1 里程碑规划

| 阶段          | 周期     | 交付物        | 关键任务                   |
| ----------- | ------ | ---------- | ---------------------- |
| **Phase 1** | Week 1 | 数据仓库 + ETL | 完成维度建模，实现数据清洗入库        |
| **Phase 2** | Week 2 | API 服务     | 完成核心接口开发，部署到 Railway   |
| **Phase 3** | Week 3 | 可视化 + 文档   | 完成 Streamlit 应用，编写技术文档 |
| **Phase 4** | Week 4 | 优化 + 演示    | 性能调优，准备面试演示脚本          |

### 5.2 风险与应对

| 风险                   | 可能性 | 影响 | 应对措施                    |
| -------------------- | --- | -- | ----------------------- |
| Kaggle Notebook 内存不足 | 中   | 高  | 减小 chunksize，只处理单月数据    |
| Supabase 免费额度超限      | 低   | 中  | 监控存储与数据库用量，清理原始数据保留聚合数据 |
| Railway 冷启动延迟        | 中   | 低  | 配置健康检查探针，保持最小实例运行       |
| 数据质量问题导致分析偏差         | 中   | 高  | 增加数据质量检查环节，输出校验报告       |

***

## 第六章 附录

### 6.1 术语表

| 术语   | 说明                                  |
| ---- | ----------------------------------- |
| ETL  | Extract-Transform-Load，数据抽取-转换-加载   |
| OLAP | Online Analytical Processing，在线分析处理 |
| RFM  | Recency-Frequency-Monetary，用户价值分层模型 |
| 星型模型 | 事实表居中，维度表环绕的维度建模方式                  |
| 物化视图 | 预计算并存储的查询结果，加速读取                    |
| 代理键  | 数据库生成的无业务含义的主键                      |

### 6.2 参考资料

- Supabase 文档：<https://supabase.com/docs>
- FastAPI 文档：<https://fastapi.tiangolo.com>
- Streamlit 文档：<https://docs.streamlit.io>
- 《The Data Warehouse Toolkit》（维度建模经典）

