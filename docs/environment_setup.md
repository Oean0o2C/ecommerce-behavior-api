# 环境配置详细步骤

本项目包含 ETL、API 服务、可视化三部分，在项目根目录统一管理 Python 环境与 `.env`。

## 1. 安装基础环境

- 安装 Python 3.11+
- 安装 Git

验证：

```
python --version
```

## 2. 创建虚拟环境（项目根目录）

在项目根目录执行：

```
python -m venv .venv
```

激活（PowerShell）：

```
.\.venv\Scripts\Activate.ps1
```

若提示执行策略错误：

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

然后重新执行激活命令。

## 3. 安装依赖

**所有依赖（前后端）已统一放在项目根目录的 `requirements.txt` 中。**

```bash
# 确保已激活虚拟环境，然后在项目根目录执行
pip install -r requirements.txt
```

这将一次性安装所有需要的依赖，包括：
- **后端**：FastAPI、SQLAlchemy、psycopg 等
- **前端**：Streamlit、Plotly、openpyxl 等
- **数据处理**：Pandas、NumPy、tqdm 等

**注意**：不需要单独安装 backend 或 frontend 的依赖，根目录的 `requirements.txt` 已包含全部依赖。

## 4. 配置 Supabase 与 `DATABASE_URL`

### 4.1 本仓库采用的连接方式

- **Session pooler**：在 Supabase Dashboard → **Project Settings** → **Database** → **Connection string** 中，选择与 **Session mode** 对应的连接串（主机形如 `*.pooler.supabase.com`，端口 **5432**）。
- **SSL**：在连接串末尾追加 `?sslmode=require`（若控制台生成的 URI 已含查询参数，用 `&sslmode=require` 拼接）。

**Transaction pooler**（常见端口 **6543**）不是本仓库的默认选项：异步栈使用 asyncpg 时与 Transaction 模式下的预编译语句行为易冲突；除非你按 [Supabase：Connecting to Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres) 单独调整 asyncpg 的语句缓存，否则请继续用 Session pooler。

### 4.2 写入 `.env`

在项目根目录**新建**文件 `.env`（勿提交到 Git），例如：

**FastAPI（同步，psycopg）**

```
DATABASE_URL=postgresql+psycopg://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-xxx.pooler.supabase.com:5432/postgres?sslmode=require
```

**ETL（`etl/local_import.py`）**  

使用**同一条** `DATABASE_URL` 即可：脚本内部会使用 `postgresql+psycopg://`（psycopg3），与 Session pooler 配套。

将 `[YOUR-PASSWORD]` 替换为创建 Supabase 项目时设置的**数据库密码**（非登录密码或 API Key）。

### 4.3 驱动分工（与仓库一致）

| 用途 | 驱动 | 说明 |
| --- | --- | --- |
| FastAPI | `psycopg` 3（`postgresql+psycopg://`） | SQLAlchemy 2 同步引擎 |
| `local_import.py` | `psycopg` 3（`postgresql+psycopg://`） | pandas `to_sql` 同步写入 |

## 5. 本地验证与部署约定

**生产部署**：后端 **Railway**（FastAPI），前端 **Streamlit Cloud**（Streamlit），与根目录 `README.md` §3.4 一致。线上环境变量中配置同一套 `DATABASE_URL`（Session pooler）及 API 根地址供前端调用。

### 5.1 本地启动 API

在项目根目录执行（需已配置 `.env` 中的 `DATABASE_URL`）：

```
uvicorn backend.app.main:app --reload
```

浏览器访问：http://127.0.0.1:8000/health 、http://127.0.0.1:8000/docs  

### 5.2 本地运行 Streamlit

```
streamlit run frontend/app.py
```

侧边栏 **API Base URL** 填 `http://127.0.0.1:8000`；对外访问以 **Streamlit Cloud** 部署为准。

## 6. 常见问题

- `ModuleNotFoundError`：确认已激活虚拟环境并执行 `pip install -r requirements.txt`。
- 无法连接数据库：核对 `DATABASE_URL`；确认 Supabase 项目未暂停；密码与端口 **5432**、**Session pooler** 主机一致；保留 `sslmode=require`。
- PowerShell 执行策略：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

---

## 7. 部署前核对清单（Supabase）

| 序号 | 项 | 操作 |
| --- | --- | --- |
| 1 | `.env` / 部署平台环境变量 | `DATABASE_URL` 使用 **Session pooler** 连接串（`*.pooler.supabase.com:5432`）+ `sslmode=require` |
| 2 | FastAPI | `DATABASE_URL` 使用 `postgresql+psycopg://...` |
| 3 | `etl/local_import.py` | 共用同一 `DATABASE_URL`；脚本内使用 `postgresql+psycopg://` |
| 4 | `docs/sql/*.sql` | 生产库在 Supabase **SQL Editor** 按 `docs/README.md` **完整执行**（含 `schema.sql` 全量对象）；依赖的扩展在 **Database → Extensions** 中启用 |
| 5 | 密钥 | 含密码的 `.env` 不提交 Git；部署平台用私密环境变量注入 |
| 6 | 用量 | 在 Dashboard 查看 **Database** 存储与连接用量 |
