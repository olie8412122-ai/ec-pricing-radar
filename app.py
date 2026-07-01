import streamlit as st
import json
import urllib.request
import google.generativeai as genai

# 網頁基本設定
st.set_page_config(page_title="🇹🇼 台灣電商選品與爆款趨勢雷達", layout="wide", page_icon="📈")

# --- 【雲端金鑰安全配置】 ---
# 為了方便您分享給別人，您可以直接將金鑰填入下方，或者讓使用者在側邊欄自行輸入
DEFAULT_GEMINI_KEY = "AQ.Ab8RN6JltjA1tAAue1RW9HQCUeAgYrsnZMgQZOfMHHnlPUuK1A"
DEFAULT_SERPER_KEY = "7ea4340769006545e96fdaefe5d949764d985769"

st.sidebar.header("🔑 雲端系統金鑰設定")
st.sidebar.markdown("💡 *若後台已配置金鑰，留空即可直接運作。*")
user_gemini = st.sidebar.text_input("Gemini API Key (選填)", type="password")
user_serper = st.sidebar.text_input("Serper (Google) Key (選填)", type="password")

FINAL_GEMINI_KEY = user_gemini.strip() if user_gemini else DEFAULT_GEMINI_KEY
FINAL_SERPER_KEY = user_serper.strip() if user_serper =="" else (user_serper.strip() if user_serper else DEFAULT_SERPER_KEY)

# --- 核心大腦：呼叫 Google Serper 搜尋引擎 ---
def call_serper_search(query_string, serper_key):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": serper_key.strip(), "Content-Type": "application/json"}
    payload = json.dumps({"q": query_string, "gl": "tw", "hl": "zh-tw"}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8')).get('organic', [])
    except Exception as e:
        st.error(f"⚠️ 雲端搜尋引擎連線失敗: {e}")
        return []

# --- 核心大腦：呼叫 Gemini AI 智囊團 ---
def call_gemini_brain(prompt_text, gemini_key):
    try:
        genai.configure(api_key=gemini_key.strip())
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt_text)
        return response.text.replace("```json", "").replace("```", "").strip()
    except Exception as e:
        st.error(f"⚠️ Gemini AI 運算超時或額度限制: {e}")
        return None


# === 主網頁介面 UI ===
st.title("📈 台灣電商選品與爆款趨勢雷達 (全雲端商用版)")
st.markdown("本工具整合 **Google 搜尋動態、長尾藍海詞篩選、主流電商實時比價**，由 Gemini AI 進行全自動化市場選品診斷。")
st.divider()

# 使用者輸入核心
col_in1, col_in2 = st.columns([2, 1])
with col_in1:
    target_keyword = st.text_input("🎯 請輸入您想評估或探索的電商品類 / 商品名稱：", placeholder="例如：行動電源、筆電支架、露營美學")
with col_in2:
    estimated_cost = st.number_input("💰 您的預期進貨成本價 (TWD，選填)：", min_value=0, value=0)

if st.button("🚀 啟動全網選品雷達全面大數據分析", type="primary"):
    if not target_keyword:
        st.warning("請先輸入想探索的商品名稱！")
    else:
        with st.spinner("⏳ 正在啟動三大核心雷達模組，實時分析台灣市場大數據..."):
            
            # --- 🛠️ 模組一：Google 趨勢與市場需求分析 ---
            # 透過搜尋「趨勢」相關網頁與新聞，交由 AI 評估目前的市場熱度
            trend_raw_data = call_serper_search(f"{target_keyword} 趨勢 流行 2026", FINAL_SERPER_KEY)
            
            # --- 🛠️ 模組二：藍海長尾關鍵字篩選 ---
            # 搜尋相關的消費者搜尋詞，由 AI 抓出具備高潛力、低競爭的藍海市場
            keyword_raw_data = call_serper_search(f"{target_keyword} 推薦 比較 PTT Dcard", FINAL_SERPER_KEY)
            
            # --- 🛠️ 模組三：實時電商比價與利潤精算 ---
            # 直接去 momo, PChome, 蝦皮抓取當前的商品真實標價
            market_raw_data = call_serper_search(f"{target_keyword} 價格 (site:momoshop.com.tw OR site:24h.pchome.com.tw OR site:shopee.tw)", FINAL_SERPER_KEY)
            
            # === 將大數據打包交給 Gemini 進行全自動交叉診斷 ===
            summary_data = f"""
            【分析目標商品】: {target_keyword}
            【預期進貨成本】: {estimated_cost} 元
            
            【模組一原始數據(趨勢觀測)】:
            {str(trend_raw_data[:4])}
            
            【模組二原始數據(消費者痛點)】:
            {str(keyword_raw_data[:4])}
            
            【模組三原始數據(主流電商售價)】:
            {str(market_raw_data[:5])}
            """
            
            prompt = f"""
            你是精通台灣電商（momo、蝦皮）的頂尖選品大師與數據分析師。請根據提供的大數據，嚴格以下列 JSON 格式回覆：
            {{
                "market_trend": "一句話總結該品類目前在台灣市場的熱度與動向(例如：正值夏季露營熱潮，搜尋量暴增)",
                "potential_rank": "根據數據給予該商品綜合潛力評分(例如：高潛力、中等紅海、極高風險紅海)",
                "blue_ocean_keywords": [
                    {{"keyword": "潛力長尾詞1", "reason": "為什麼這個詞是藍海？消費者有什麼未滿足的痛點？"}},
                    {{"keyword": "潛力長尾詞2", "reason": "消費者關注的特點"}}
                ],
                "competitor_prices": [
                    {{"platform": "電商平台名稱", "price": 數字型態售價, "title": "抓取到的商品標題"}}
                ],
                "pricing_strategy": "如果我要賣這個商品，Gemini 給予的具體定價與行銷策略建議(必須提及利潤率與開立發票5%營業稅的考量)"
            }}
            
            數據源：
            {summary_data}
            """
            
            ai_response_text = call_gemini_brain(prompt, FINAL_GEMINI_KEY)
            
            if ai_response_text:
                try:
                    result = json.loads(ai_response_text)
                    
                    st.success("🎉 全網市場情報雷達分析完成！")
                    
                    # --- 顯示功能一：市場趨勢動向 ---
                    st.header("📊 功能一：市場趨勢與熱度動向")
                    col_t1, col_t2 = st.columns([3, 1])
                    with col_t1:
                        st.info(f"🔎 **市場最新動態現況**：\n{result.get('market_trend')}")
                    with col_t2:
                        st.metric(label="🎯 綜合潛力評估", value=result.get('potential_rank'))
                    
                    st.divider()
                    
                    # --- 顯示功能二：爆款潛力關鍵字藍海分析 ---
                    st.header("🚀 功能二：爆款潛力長尾關鍵字（藍海市場）")
                    st.markdown("💡 *提示：避開大關鍵字，從以下 AI 篩選出的長尾痛點切入，最容易做出差異化爆款！*")
                    for kv in result.get('blue_ocean_keywords', []):
                        with st.expander(f"📌 潛力選品核心詞：**{kv.get('keyword')}**"):
                            st.write(f"**AI 藍海市場診斷分析**：{kv.get('reason')}")
                            
                    st.divider()
                    
                    # --- 顯示功能三：實時電商比價與財務定價水單 ---
                    st.header("💰 功能三：主流電商實時行情與財務定價策略")
                    
                    # 算平均價
                    prices = [item.get("price") for item in result.get('competitor_prices', []) if isinstance(item.get("price"), (int, float))]
                    avg_p = sum(prices) / len(prices) if prices else 0
                    
                    col_p1, col_p2 = st.columns([2, 3])
                    with col_p1:
                        st.subheader("🛒 實時台灣市場現況")
                        for item in result.get('competitor_prices', []):
                            st.write(f"* **{item.get('platform')}**： NT$ {item.get('price', 0):,} 元 — *{item.get('title')[:18]}...*")
                        if avg_p > 0:
                            st.info(f"💡 當前全台電商平均行情價：**NT$ {round(avg_p):,} 元**")
                            
                    with col_p2:
                        st.subheader("📋 機器人建議定價明細 (內含5%發票稅)")
                        
                        # 計算市場行情策略
                        market_suggested = round(avg_p * 0.95) if avg_p > 0 else 0
                        
                        if market_suggested > 0:
                            st.markdown(f"""
                            | 定價策略 | 建議零售價 (含稅) | 開立發票基礎 (銷售額) | 應繳納之 5% 營業稅 |
                            | :--- | :--- | :--- | :--- |
                            | **策略 A：迎合市場行情 (均價95%)** | **NT$ {market_suggested:,} 元** | NT$ {round(market_suggested/1.05):,} 元 | NT$ {market_suggested - round(market_suggested/1.05):,} 元 |
                            """)
                            
                        # 如果有輸入成本，計算成本利潤策略（預設抓 20% 利潤率）
                        if estimated_cost > 0:
                            cost_suggested = round(estimated_cost * 1.20 * 1.05)
                            sales_amount = round(cost_suggested / 1.05)
                            tax_amount = cost_suggested - sales_amount
                            st.markdown(f"""
                            | 定價策略 | 建議零售價 (含稅) | 開立發票基礎 (銷售額) | 應繳納之 5% 營業稅 |
                            | :--- | :--- | :--- | :--- |
                            | **策略 B：守住基礎利潤 (成本+20%)** | **NT$ {cost_suggested:,} 元** | NT$ {sales_amount:,} 元 | NT$ {tax_amount:,} 元 |
                            """)
                            
                    st.light_box = st.warning(f"💡 **AI 實戰定價與操盤方針**：\n{result.get('pricing_strategy')}")
                    
                except Exception as parse_error:
                    st.error("JSON 解析失敗，可能因為雲端大數據過於龐大。請再點擊一次按鈕重新產生。")
                    st.caption(f"原始回傳數據：{ai_response_text}")
