# 部署指南

本指南将详细说明如何将电商用户行为数据分析平台部署到云服务，包括后端（FastAPI）部署到Railway和前端（Streamlit）部署到Streamlit Cloud。

## 1. 后端部署（Railway）

### 1.1 准备工作

1. **创建Railway账户**：访问 [Railway](https://railway.app/) 并创建账户。
2. **连接GitHub仓库**：在Railway中连接包含项目代码的GitHub仓库。
3. **配置环境变量**：在Railway项目中添加以下环境变量：
   - `DATABASE_URL`：Supabase数据库连接字符串

### 1.2 部署步骤

1. **创建新的Railway项目**：
   - 点击"New Project" -> "Deploy from GitHub repo"
   - 选择你的项目仓库
   - 选择`backend`目录作为部署目标

2. **配置构建和启动**：
   - Railway会自动检测到Python项目并使用`requirements.txt`安装依赖
   - 确保`Procfile`文件存在于`backend`目录中

3. **部署**：
   - Railway会自动开始部署过程
   - 部署完成后，你将获得一个公共URL

## 2. 前端部署（Streamlit Cloud）

### 2.1 准备工作

1. **创建Streamlit Cloud账户**：访问 [Streamlit Cloud](https://streamlit.io/cloud) 并创建账户。
2. **连接GitHub仓库**：在Streamlit Cloud中连接包含项目代码的GitHub仓库。

### 2.2 部署步骤

1. **创建新的Streamlit应用**：
   - 点击"New app" -> "From existing repo"
   - 选择你的项目仓库
   - 选择`frontend`目录作为部署目标
   - 填写主文件路径：`app.py`

2. **配置环境变量**：
   - 在Streamlit Cloud应用设置中添加以下环境变量：
     - `API_BASE_URL`：后端API的公共URL（从Railway获取）

3. **部署**：
   - Streamlit Cloud会自动开始部署过程
   - 部署完成后，你将获得一个公共URL

## 3. 数据库配置（Supabase）

### 3.1 准备工作

1. **创建Supabase账户**：访问 [Supabase](https://supabase.com/) 并创建账户。
2. **创建新的Supabase项目**：在Supabase中创建一个新的项目。

### 3.2 数据库设置

1. **执行SQL脚本**：
   - 在Supabase的SQL Editor中，按顺序执行以下脚本：
     1. `docs/sql/schema.sql`：创建表和物化视图
     2. `docs/sql/generated_columns_triggers.sql`：创建触发器
     3. `docs/sql/indexes_constraints.sql`：创建索引和约束

2. **获取数据库连接字符串**：
   - 在Supabase项目的"Settings" -> "Database"中获取数据库连接字符串
   - 将连接字符串配置到Railway的环境变量中

## 4. 测试部署

1. **测试后端API**：
   - 访问Railway部署的后端API URL，例如：`https://your-backend-url.railway.app/health`
   - 确认API返回健康状态

2. **测试前端应用**：
   - 访问Streamlit Cloud部署的前端应用URL
   - 确认应用能够正常加载并显示数据

3. **测试数据流程**：
   - 运行ETL流程，将数据导入Supabase数据库
   - 确认前端应用能够显示导入的数据

## 5. 常见问题及解决方案

### 5.1 后端部署问题

- **数据库连接失败**：检查`DATABASE_URL`环境变量是否正确配置
- **依赖安装失败**：确保`requirements.txt`文件包含所有必要的依赖
- **端口配置错误**：确保`Procfile`中的端口配置正确

### 5.2 前端部署问题

- **API调用失败**：检查`API_BASE_URL`环境变量是否正确配置
- **依赖安装失败**：确保`requirements.txt`文件包含所有必要的依赖
- **数据显示错误**：检查后端API是否正常运行

### 5.3 数据库问题

- **表结构创建失败**：确保SQL脚本执行顺序正确
- **数据导入失败**：检查数据库连接字符串和权限设置
- **查询性能问题**：确保创建了必要的索引

## 6. 监控和维护

- **Railway监控**：使用Railway的日志和监控功能查看后端服务状态
- **Streamlit Cloud监控**：使用Streamlit Cloud的日志功能查看前端应用状态
- **Supabase监控**：使用Supabase的Dashboard监控数据库性能

## 7. 扩展和升级

- **代码更新**：推送到GitHub仓库后，Railway和Streamlit Cloud会自动重新部署
- **依赖更新**：更新`requirements.txt`文件后，重新部署应用
- **数据库扩展**：根据需要在Supabase中调整数据库配置
