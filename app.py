import streamlit as st
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import yaml
import re
from datetime import datetime, timedelta
from main import run_aggregator
from core.processing import Processor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="AI 財經科技情報站",
    page_icon="📈",
    layout="wide"
)

# --- 核心視覺重構 (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #1A202C; color: #E2E8F0; }
    header {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    h1 { padding-top: 0 !important; font-weight: 800 !important; }
    [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #FFFFFF1A; }
    .stMarkdown, .stButton, .stMetric, [data-testid="stVerticalBlock"] > div { text-align: left !important; align-items: flex-start !important; }
    .metric-container { background: #2D3748; padding: 1.2rem; border-radius: 12px; border: 1px solid #FFFFFF1A; margin-top: 0.5rem; margin-bottom: 1rem; }
    .metric-label { font-size: 0.85rem; color: #A0AEC0; margin-bottom: 0.2rem; }
    .metric-value { font-size: 3.8rem; font-weight: 800; color: #0BC5EA; line-height: 1; }
    .metric-delta { font-size: 0.95rem; margin-top: 0.3rem; }
    .delta-up { color: #48BB78; }
    .delta-down { color: #EF4444; }
    .update-time { font-size: 0.7rem !important; color: #718096; margin-bottom: 4px; display: block; }
    .summary-box { background: #2D3748; padding: 1rem; border-radius: 10px; border-left: 4px solid #3182CE; margin-bottom: 1rem; }
    
    /* 視覺魔法：將單位切換列鑲嵌至圖表左上角 */
    div[data-testid="stPlotlyChart"] {
        margin-top: -45px !important;
        position: relative;
        z-index: 0;
    }
    .unit-ctrl-container {
        position: relative;
        z-index: 10;
        width: 150px;
    }
    
    @media (max-width: 768px) {
        [data-testid="stHorizontalBlock"] { display: flex; flex-direction: column-reverse; }
    }
    </style>
    """, unsafe_allow_html=True)

def load_config():
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_trends():
    trend_file = 'data/sentiment_trends.json'
    if os.path.exists(trend_file):
        try:
            with open(trend_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: return []
    return []

def load_summary_history():
    history_file = 'data/summaries_history.json'
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
                def extract_time(s):
                    match = re.search(r"🕒 更新時間：([\d-]+\s[\d:]+)", s)
                    return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M") if match else datetime.min
                now = datetime.now()
                cutoff = now - timedelta(hours=48)
                valid_history = [item for item in history if extract_time(item) >= cutoff]
                if len(valid_history) < len(history):
                    with open(history_file, 'w', encoding='utf-8') as f:
                        json.dump(valid_history, f, ensure_ascii=False, indent=2)
                return sorted(list(set(valid_history)), key=extract_time, reverse=True)
        except: return []
    return []

def save_summary_history(new_item=None):
    history_file = 'data/summaries_history.json'
    os.makedirs('data', exist_ok=True)
    current_history = load_summary_history()
    if new_item and new_item not in current_history:
        current_history.insert(0, new_item)
    def extract_time(s):
        match = re.search(r"🕒 更新時間：([\d-]+\s[\d:]+)", s)
        return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M") if match else datetime.min
    final_history = sorted(list(set(current_history)), key=extract_time, reverse=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(final_history, f, ensure_ascii=False, indent=2)
    return final_history

def safe_run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# --- Logic ---
config = load_config()
st.sidebar.title("💎 情報儀表板")
app_mode = st.sidebar.radio("切換模式", ["財經概覽", "測試助理", "翻譯助理"])

if app_mode == "財經概覽":
    summary_history = load_summary_history()
    
    if 'auto_checked' not in st.session_state:
        st.session_state['auto_checked'] = True
        should_update = True
        if summary_history:
            match = re.search(r"🕒 更新時間：([\d-]+\s[\d:]+)", summary_history[0])
            if match:
                last_update = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M")
                should_update = (datetime.now() - last_update).total_seconds() / 3600 >= 1.0
        if should_update:
            with st.spinner("獲取情報中..."):
                summary, _ = safe_run_async(run_aggregator())
                if summary:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    styled = f"<div class='update-time'>🕒 更新時間：{now_str}</div>\n\n{summary}\n\n---"
                    summary_history = save_summary_history(styled)
                    st.rerun()

    st.title("🗞️ 財經與科技情報站")
    col1, col2 = st.columns([1.8, 1])

    with col1:
        st.subheader("💡 核心動態摘要")
        if st.button("🚀 刷新數據"):
            with st.spinner("分析中..."):
                summary, news = safe_run_async(run_aggregator())
                if summary:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                    styled = f"<div class='update-time'>🕒 更新時間：{now_str}</div>\n\n{summary}\n\n---"
                    summary_history = save_summary_history(styled)
                    st.session_state['last_news_items'] = news
                    st.rerun()
        for hist in summary_history[:5]:
            st.markdown(f"<div class='summary-box'>{hist}</div>", unsafe_allow_html=True)

    with col2:
        trends = load_trends()
        if trends:
            st.subheader("📈 市場信心走勢")
            df = pd.DataFrame(trends)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df['val'] = df['average_sentiment'].apply(lambda x: round((x + 1) * 50) if -1.0 <= x <= 1.0 else x)
            
            latest_val = df.iloc[-1]['val']
            prev_val = df.iloc[-2]['val'] if len(df) > 1 else 50
            diff = latest_val - prev_val
            delta_class = "delta-up" if diff >= 0 else "delta-down"
            delta_sign = "+" if diff >= 0 else ""
            
            st.markdown(f"""
                <div class='metric-container'>
                    <div class='metric-label'>最新信心指數 (Live)</div>
                    <div class='metric-value'>{latest_val:.0f}</div>
                    <div class='metric-delta {delta_class}'>{delta_sign}{diff:.0f} pts (相對前次)</div>
                </div>
            """, unsafe_allow_html=True)

            # --- 單位切換列 ---
            st.markdown("<div class='unit-ctrl-container'>", unsafe_allow_html=True)
            view_unit = st.radio("單位", ["原始", "小時", "天"], horizontal=True, index=0, label_visibility="collapsed", key="v_unit")
            st.markdown("</div>", unsafe_allow_html=True)
            
            plot_df = df.copy()
            if view_unit == "小時":
                plot_df['timestamp'] = plot_df['timestamp'].map(lambda x: x.replace(minute=0, second=0, microsecond=0))
                plot_df = plot_df.groupby('timestamp')['val'].mean().reset_index()
                x_fmt = "%m/%d %H:%M"
            elif view_unit == "天":
                plot_df['timestamp'] = plot_df['timestamp'].map(lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0))
                plot_df = plot_df.groupby('timestamp')['val'].mean().reset_index()
                x_fmt = "%m/%d"
            else:
                x_fmt = "%H:%M"
            
            plot_df = plot_df.sort_values('timestamp')
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=plot_df['timestamp'], y=plot_df['val'],
                mode='lines+markers', fill='tozeroy',
                fillcolor='rgba(11, 197, 234, 0.15)',
                line=dict(width=4, color='#0BC5EA', shape='spline'),
                marker=dict(size=8, color='#0BC5EA', line=dict(width=1.5, color='#FFFFFF')),
                connectgaps=True, name='指數'
            ))

            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=50, b=0), height=300, showlegend=False,
                xaxis=dict(
                    showgrid=True, gridcolor='rgba(255,255,255,0.08)',
                    tickfont=dict(size=9, color='#718096'),
                    tickformat=x_fmt, type='date'
                ),
                yaxis=dict(
                    showgrid=True, gridcolor='rgba(255,255,255,0.08)',
                    tickfont=dict(size=9, color='#718096'),
                    range=[0, 100], dtick=25, zeroline=False,
                    fixedrange=True # 縮放時鎖定 Y 軸，僅允許縮放時間軸
                ),
                dragmode='pan', # 預設為平移模式
                hovermode='x unified'
            )
            # 啟用 Scroll Zoom 支援滾輪與雙指捏合縮放
            st.plotly_chart(fig, use_container_width=True, config={
                'scrollZoom': True, 
                'displayModeBar': False,
                'showTips': False
            })

        st.markdown("---")
        st.subheader("🔥 重大焦點列表")
        if 'last_news_items' in st.session_state and st.session_state['last_news_items']:
            for item in st.session_state['last_news_items'][:12]:
                st.markdown(f"##### <a href='{item['link']}' style='color:#E2E8F0; text-decoration:none;'>{item['title']}</a>", unsafe_allow_html=True)
                st.caption(f"🕒 {item.get('display_time', '即時')} | {item['source']}")
                st.markdown("---")
        else: st.info("請點擊刷新以載入新聞列表。")

elif app_mode == "測試助理":
    st.title("🧪 AI 測試助理")
    user_req = st.text_area("需求描述：", height=200)
    if st.button("啟動分析"): st.info("分析中...")

elif app_mode == "翻譯助理":
    st.title("🔤 AI 翻譯官")
    user_input = st.text_area("原文：", height=300)
    if st.button("翻譯"): st.info("翻譯中...")

st.markdown("<br><p style='text-align:center; color:#4A5568; font-size:0.7rem;'>Powered by Gemini 2.5 Flash</p>", unsafe_allow_html=True)
