import os
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import time

# 设置页面标题和布局
st.set_page_config(
    page_title="电商用户行为数据分析平台",
    page_icon="📊",
    layout="wide"
)

# 初始化 session state
if 'api_base_url' not in st.session_state:
    # 优先读取环境变量（部署时用）
    deployed_url = os.getenv("API_BASE_URL")
    
    if deployed_url:
        # 线上环境：用 Railway 地址
        st.session_state.api_base_url = deployed_url
    else:
        # 本地开发环境：用 localhost
        st.session_state.api_base_url = "http://localhost:8000"

# 辅助函数：调用API（带缓存）
@st.cache_data(ttl=600, show_spinner=False)  # 缓存10分钟，不使用持久化

def call_api_cached(base_url, endpoint, params=None):
    """带缓存的API调用"""
    try:
        full_url = f"{base_url}/api/v1{endpoint}"
        response = requests.get(full_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# 辅助函数：并行调用多个API
def call_apis_parallel(api_calls):
    """并行调用多个API"""
    import concurrent.futures
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        # 提交所有API调用
        future_to_api = {executor.submit(call_api_cached, url, endpoint, params): key 
                        for key, (url, endpoint, params) in api_calls.items()}
        
        # 收集结果
        for future in concurrent.futures.as_completed(future_to_api):
            key = future_to_api[future]
            try:
                results[key] = future.result()
            except Exception as e:
                results[key] = {"error": str(e)}
    
    return results

def call_api(endpoint, params=None):
    """调用API（实时）"""
    try:
        full_url = f"{st.session_state.api_base_url}/api/v1{endpoint}"
        response = requests.get(full_url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API调用失败: {str(e)}")
        return None

# 辅助函数：导出数据
def export_to_csv(data, filename):
    """导出数据为CSV"""
    if data:
        df = pd.DataFrame(data)
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        return csv
    return None

def export_to_excel(data, filename):
    """导出数据为Excel"""
    if data:
        df = pd.DataFrame(data)
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='数据')
        return output.getvalue()
    return None

# 侧边栏
with st.sidebar:
    st.title("⚙️ 配置")
    
    # API Base URL 配置
    st.subheader("API 配置")
    api_url = st.text_input(
        "API Base URL",
        value=st.session_state.api_base_url,
        placeholder="http://localhost:8000"
    )
    if api_url != st.session_state.api_base_url:
        st.session_state.api_base_url = api_url
        st.success("API地址已更新")
    
    # 测试连接
    if st.button("🔄 测试连接"):
        with st.spinner("正在测试连接..."):
            try:
                response = requests.get(f"{st.session_state.api_base_url}/health", timeout=5)
                if response.status_code == 200:
                    st.success("✅ 连接成功")
                else:
                    st.error(f"❌ 连接失败: {response.status_code}")
            except Exception as e:
                st.error(f"❌ 连接失败: {str(e)}")
    
    st.markdown("---")
    
    # 时间范围选择
    st.title("📅 时间范围")
    
    # 快速选择
    col1, col2 = st.columns(2)
    with col1:
        if st.button("最近7天"):
            st.session_state.start_date = date.today() - timedelta(days=7)
            st.session_state.end_date = date.today()
            st.rerun()
    with col2:
        if st.button("最近30天"):
            st.session_state.start_date = date.today() - timedelta(days=30)
            st.session_state.end_date = date.today()
            st.rerun()
    
    # 日期选择器
    if 'start_date' not in st.session_state:
        st.session_state.start_date = date.today() - timedelta(days=30)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = date.today()
    
    # 日期选择器
    # 先获取当前的开始日期
    current_start = st.session_state.start_date
    
    # 开始日期选择器
    start_date = st.date_input("开始日期", current_start)
    
    # 结束日期选择器 - 允许选择早于当前日期但晚于开始日期的日期
    # 这样当开始日期选择2019年时，结束日期可以选择2019年的日期
    min_end_date = start_date
    max_end_date = date.today()
    
    # 计算默认的结束日期
    # 当开始日期改变时，重置结束日期为开始日期
    if start_date != current_start:
        default_end_date = start_date
    elif 'end_date' not in st.session_state or st.session_state.end_date < start_date:
        default_end_date = start_date
    else:
        default_end_date = st.session_state.end_date
    
    # 结束日期选择器
    end_date = st.date_input(
        "结束日期", 
        default_end_date, 
        min_value=min_end_date,
        max_value=max_end_date
    )
    
    # 时间范围验证
    today = date.today()
    max_date_range = 365  # 最大时间范围为1年
    
    # 检查是否选择未来日期
    if start_date > today or end_date > today:
        st.warning("⚠️ 警告：您选择了未来日期，可能无数据")
    
    # 检查时间范围是否过大
    if (end_date - start_date).days > max_date_range:
        st.warning(f"⚠️ 警告：时间范围过大，建议不超过{max_date_range}天")
    
    # 检查开始日期是否晚于结束日期
    if start_date > end_date:
        st.error("❌ 错误：开始日期不能晚于结束日期")
        # 重置为默认值
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()
    
    st.session_state.start_date = start_date
    st.session_state.end_date = end_date
    
    st.markdown("---")
    
    # 数据导出
    st.title("📥 数据导出")
    export_format = st.selectbox("导出格式", ["CSV", "Excel"])

# 主页面标题
st.title("📊 电商用户行为数据分析平台")
st.markdown(f"*数据时间范围: {start_date} 至 {end_date}*")

# 并行加载所有API数据
with st.spinner("正在加载数据..."):
    api_calls = {
        "overview": (
            st.session_state.api_base_url,
            "/sales/overview",
            {"start_date": start_date, "end_date": end_date}
        ),
        "funnel": (
            st.session_state.api_base_url,
            "/user/funnel",
            {"start_date": start_date, "end_date": end_date}
        )
    }
    
    # 并行调用API
    api_results = call_apis_parallel(api_calls)
    
    # 获取结果
    overview_data = api_results.get("overview")
    funnel_data = api_results.get("funnel")

# 创建标签页
tab1, tab2, tab3, tab4 = st.tabs(["📈 销售概览", "📊 品类分析", "🎯 用户漏斗", "🏆 热销商品"])

# ========== 标签页1: 销售概览 ==========
with tab1:
    st.header("销售概览")
    
    # 销售概览卡片
    if overview_data and overview_data.get("code") == 200:
        data = overview_data.get("data", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 GMV", f"¥{data.get('gmv', 0):,.2f}")
        with col2:
            st.metric("📦 订单数", f"{data.get('order_count', 0):,}")
        with col3:
            st.metric("👥 UV", f"{data.get('uv', 0):,}")
        with col4:
            st.metric("📈 转化率", f"{data.get('conversion_rate', 0):.2%}")
        
        # 导出销售概览数据
        if st.button("📥 导出销售概览", key="export_overview"):
            csv_data = export_to_csv([data], "销售概览")
            if csv_data:
                st.download_button(
                    label="下载 CSV",
                    data=csv_data,
                    file_name=f"销售概览_{start_date}_{end_date}.csv",
                    mime="text/csv"
                )
    else:
        st.warning("暂无销售概览数据")
    
    st.markdown("---")
    
    # 销售趋势图表
    st.subheader("销售趋势")
    granularity = st.selectbox("时间粒度", ["day", "week", "month"], index=0, key="trend_granularity")
    
    with st.spinner("正在加载趋势数据..."):
        trend_data = call_api_cached(
            st.session_state.api_base_url,
            "/sales/trend",
            {
                "granularity": granularity,
                "start_date": start_date,
                "end_date": end_date
            }
        )
    
    if trend_data and trend_data.get("code") == 200:
        trend = trend_data.get("data", {}).get("trend", [])
        if trend:
            df_trend = pd.DataFrame(trend)
            
            # 创建双轴图表
            fig = px.line(df_trend, x="date", y=["gmv", "orders"], 
                         title=f"销售趋势 ({granularity})",
                         labels={"value": "数值", "date": "日期", "variable": "指标"})
            st.plotly_chart(fig, width="stretch")
            
            # 显示数据表格
            with st.expander("查看原始数据"):
                st.dataframe(df_trend, width="stretch")
                
                # 导出趋势数据
                csv_data = export_to_csv(trend, "销售趋势")
                if csv_data:
                    st.download_button(
                        label="📥 导出趋势数据 (CSV)",
                        data=csv_data,
                        file_name=f"销售趋势_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("该时间范围内暂无趋势数据")
    else:
        st.warning("无法获取趋势数据")

# ========== 标签页2: 品类分析 ==========
with tab2:
    st.header("品类分析")
    
    col1, col2 = st.columns(2)
    with col1:
        category_level = st.selectbox("类目层级", ["l1", "l2", "l3"], index=0)
    with col2:
        limit = st.slider("返回数量", 5, 20, 10, key="category_limit")
    
    with st.spinner("正在加载品类数据..."):
        category_data = call_api_cached(
            st.session_state.api_base_url,
            "/category/performance",
            {
                "category_level": category_level,
                "limit": limit,
                "start_date": start_date,
                "end_date": end_date
            }
        )
    
    if category_data and category_data.get("code") == 200:
        categories = category_data.get("data", {}).get("categories", [])
        if categories:
            df_category = pd.DataFrame(categories)
            
            col1, col2 = st.columns(2)
            
            # 饼图
            with col1:
                fig_pie = px.pie(df_category, values="gmv", names="name", 
                               title="品类GMV占比",
                               hole=0.3)
                # 优化标签布局，避免图例与饼图重叠
                fig_pie.update_layout(
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05,
                        font=dict(size=10)
                    ),
                    margin=dict(l=30, r=200, t=50, b=0),
                    height=400,  # 增加图表高度，让数据标签和悬停弹窗有足够空间显示
                    hovermode='closest',
                    spikedistance=100,
                    hoverlabel=dict(
                        bgcolor="white",
                        bordercolor="black",
                        font=dict(size=12),
                        align="left"
                    )
                )
                # 优化数据标签显示
                fig_pie.update_traces(
                    textposition='auto',
                    texttemplate='%{percent:.1%}',
                    textfont=dict(size=10),
                    insidetextorientation='auto',
                    hovertemplate='<b>%{label}</b><br>GMV: %{value:,.0f}<br>占比: %{percent:.1%}<extra></extra>'
                )
                st.plotly_chart(fig_pie, width="stretch")
                
            
            # 柱状图
            with col2:
                fig_bar = px.bar(df_category, x="name", y="gmv", 
                               title="品类GMV对比",
                               labels={"gmv": "GMV", "name": "品类"})
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, width="stretch")
            
            # 数据表格
            with st.expander("查看品类数据"):
                st.dataframe(df_category, width="stretch")
                
                # 导出品类数据
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = export_to_csv(categories, "品类分析")
                    if csv_data:
                        st.download_button(
                            label="📥 导出 CSV",
                            data=csv_data,
                            file_name=f"品类分析_{category_level}.csv",
                            mime="text/csv"
                        )
                with col2:
                    # Excel 导出
                    try:
                        excel_data = export_to_excel(categories, "品类分析")
                        if excel_data:
                            st.download_button(
                                label="📥 导出 Excel",
                                data=excel_data,
                                file_name=f"品类分析_{category_level}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    except Exception as e:
                        st.info("Excel导出需要安装openpyxl: pip install openpyxl")
        else:
            # 根据品类层级显示不同的提示信息
            if category_level == 'l1':
                st.info("暂无品类数据")
            else:
                st.info(f"暂无 {category_level.upper()} 层级的品类数据，请尝试选择 L1 层级")
    else:
        st.warning("无法获取品类数据")

# ========== 标签页3: 用户漏斗 ==========
with tab3:
    st.header("用户行为漏斗")
    
    if funnel_data and funnel_data.get("code") == 200:
        funnel = funnel_data.get("data", {}).get("funnel", [])
        if funnel:
            df_funnel = pd.DataFrame(funnel)
            
            # 漏斗图
            fig_funnel = px.funnel(df_funnel, x="count", y="stage", 
                                  title="用户行为漏斗",
                                  labels={"count": "用户数", "stage": "阶段"})
            st.plotly_chart(fig_funnel, width="stretch")
            
            # 转化率表格
            st.subheader("转化率详情")
            
            # 计算转化率
            conversion_data = []
            for i, row in df_funnel.iterrows():
                if i == 0:
                    conversion_rate = 100.0
                else:
                    prev_count = df_funnel.iloc[i-1]['count']
                    curr_count = row['count']
                    conversion_rate = (curr_count / prev_count * 100) if prev_count > 0 else 0
                
                conversion_data.append({
                    "阶段": row['stage'],
                    "用户数": row['count'],
                    "转化率": f"{conversion_rate:.1f}%"
                })
            
            df_conversion = pd.DataFrame(conversion_data)
            st.dataframe(df_conversion, width="stretch")
            
            # 导出漏斗数据
            if st.button("📥 导出漏斗数据", key="export_funnel"):
                csv_data = export_to_csv(funnel, "用户漏斗")
                if csv_data:
                    st.download_button(
                        label="下载 CSV",
                        data=csv_data,
                        file_name=f"用户漏斗_{start_date}_{end_date}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("暂无漏斗数据")
    else:
        st.warning("无法获取漏斗数据")

# ========== 标签页4: 热销商品 ==========
with tab4:
    st.header("热销商品")
    
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox("排序指标", ["sales", "views", "carts"], index=0)
    with col2:
        product_limit = st.slider("返回数量", 5, 20, 10, key="product_limit_slider")
    
    with st.spinner("正在加载商品数据..."):
        products_data = call_api_cached(
            st.session_state.api_base_url,
            "/products/top",
            {
                "metric": metric,
                "limit": product_limit,
                "start_date": start_date,
                "end_date": end_date
            }
        )
    
    if products_data and products_data.get("code") == 200:
        products = products_data.get("data", {}).get("products", [])
        if products:
            df_products = pd.DataFrame(products)
            
            # 商品图表
            fig_products = px.bar(df_products, x="name", y="metric_value", 
                                title=f"热销商品 ({metric})",
                                labels={"metric_value": "数值", "name": "商品"})
            fig_products.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_products, width="stretch")
            
            # 商品表格
            with st.expander("查看商品详情"):
                st.dataframe(df_products, width="stretch")
                
                # 导出商品数据
                csv_data = export_to_csv(products, "热销商品")
                if csv_data:
                    st.download_button(
                        label="📥 导出商品数据 (CSV)",
                        data=csv_data,
                        file_name=f"热销商品_{metric}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("暂无商品数据")
    else:
        st.warning("无法获取商品数据")

# 页脚
st.markdown("---")
st.markdown("© 2026 电商用户行为数据分析平台 | Powered by Streamlit & FastAPI")
