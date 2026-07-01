import streamlit as st
import json
import urllib.request
import google.generativeai as genai

# 網頁基本設定
st.set_page_config(page_title="🇹🇼 台灣電商選品與爆款趨勢雷達", layout="wide", page_icon="📈")

# --- 【金鑰完全自定義：每次手動輸入】 ---
st.sidebar.header("🔑 請填入您的專屬金鑰")
st.sidebar.markdown("⚠️ *免費版使用者請每次在下方填入可用的 KEY 才能啟動雷達。*")

user_gemini = st.sidebar.text_input("1. 輸入您的 Gemini API Key", type="password", help="請填入 AI Studio 申請的 AIzaSy... 開頭金鑰")
user_serper = st.sidebar.text_input("2. 輸入您的 Serper (Google Search) Key", type="password", help="請填入 Serper.dev 後台申請的純文字金鑰")

FINAL_GEMINI_KEY = user_gemini.strip() if user_gemini else ""
FINAL_SERPER_KEY = user_serper.strip() if user_serper else ""

# --- 核心大腦：呼叫 Google Serper 搜尋引擎 ---
def call_serper_search(query_string, serper_key):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": serper_key.strip(), "Content-Type": "application/json"}
    payload = json.dumps({"q": query_string, "gl": "tw", "hl": "zh-tw"}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=12) as response:
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
        return response.text
    except Exception as e:
        st.error(f"⚠️ Gemini AI 運算失敗: {e}")
        return None

# === 主網頁介面 UI ===
st.title("📈 台灣電商選品與爆款趨勢雷達 (自填金鑰安全版)")
st.markdown("本工具整合 **Google 搜尋動態、長尾藍海詞篩選、主流電商實時比價**，由 Gemini AI 進行全自動化市場選品診斷。")
st.divider()

# 使用者輸入核心
col_in1, col_in2 = st.columns([2, 1])
with col_in1:
    target_keyword = st.text_input("🎯 請輸入您想評估或探索的電商品類 / 商品名稱：", placeholder="例如：行動電源、筆電支架、露營美學")
with col_in2:
    estimated_cost = st.number_input("💰 您的預期進貨成本價 (TWD，選填)：", min_value=0, value=0)

if st.button("🚀 啟動全網選品雷達全面大數據分析", type="primary"):
    if not FINAL_GEMINI_KEY or not FINAL_SERPER_KEY:
        st.error("🛑 請先在左側邊欄填入正確的 Gemini Key 與 Serper Key 才能啟動雷達！")
    elif not target_keyword:
        st.warning("請先輸入想探索的商品名稱！")
    else:
        with st.spinner("⏳ 正在啟動三大核心雷達模組，實時分析台灣市場大數據..."):
            
            # 抓取三組數據並嚴格限制筆數，避免大數據撐爆格式
            trend_raw_data = call_serper_search(f"{target_keyword} 趨勢 流行 2026", FINAL_SERPER_KEY)[:3]
            keyword_raw_data = call_serper_search(f"{target_keyword} 推薦 比較 PTT Dcard", FINAL_SERPER_KEY)[:3]
            market_raw_data = call_serper_search(f"{target_keyword} 價格 (site:momoshop.com.tw OR site:24h.pchome.com.tw OR site:shopee.tw)", FINAL_SERPER_KEY)[:4]
            
            summary_data = f"""
            【分析目標商品】: {target_keyword}
            【預期進貨成本】: {estimated_cost} 元
            【趨勢數據】: {str(trend_raw_data)}
            【消費者討論】: {str(keyword_raw_data)}
            【電商價格】: {str(market_raw_data)}
            """
            
            prompt = f"""
            請根據提供的大數據進行分析。你必須「嚴格且只回覆」一個符合以下結構的 JSON 字典物件，不要包含任何 markdown 標記（絕對不要有 ```json 或 ``` 符號），確保可以直接被 json.loads 解析。
            {{
                "market_trend": "一句話總結目前的熱度與動向",
                "potential_rank": "高潛力 或 中等紅海 或 高風險紅海 (可在後面加上一小句簡短原因，例如：高潛力，但競爭開始加劇)",
                "blue_ocean_keywords": [
                    {{"keyword": "潛力詞1", "reason": "痛點分析"}}
                ],
                "competitor_prices": [
                    {{"platform": "平台名稱", "price": 數字價格, "title": "商品標題"}}
                ],
                "pricing_strategy": "具體定價與行銷策略建議"
            }}
            
            大數據源：
            {summary_data}
            """
            
            ai_response_text = call_gemini_brain(prompt, FINAL_GEMINI_KEY)
            
            if ai_response_text:
                # 【強效清洗保險機制】徹底過濾掉 AI 回傳可能夾帶的 Markdown 雜質
                clean_res = ai_response_text.strip()
                if "```" in clean_res:
                    clean_res = clean_res.split("```")
                    for part in clean_res:
                        if part.strip().startswith("{") or part.strip().startswith("["):
                            clean_res = part.strip()
                            break
                clean_res = clean_res.replace("```json", "").replace("```", "").strip()
                
                try:
                    result = json.loads(clean_res)
                    st.success("🎉 全網市場情報雷達分析完成！")
                    
                    # --- 📝 功能一：市場趨勢與熱度動向 ---
                    st.header("📊 功能一：市場趨勢與熱度動向")
                    col_t1, col_t2 = st.columns([2, 1])
                    with col_t1:
                        st.info(f"🔎 **市場最新動態現況**：\n{result.get('market_trend')}")
                    with col_t2:
                        st.markdown("### 🎯 綜合潛力評估")
                        # 採用寬大 warning 方框，字再長也百分之百能完整顯示，拒絕吃字
                        st.warning(f"**{result.get('potential_rank')}**")
                    
                    st.divider()
                    
                    # --- 🚀 功能二：爆款潛力長尾關鍵字 ---
                    st.header("🚀 功能二：爆款潛力長尾關鍵字（藍海市場）")
                    for kv in result.get('blue_ocean_keywords', []):
                        with st.expander(f"📌 潛力選品核心詞：**{kv.get('keyword')}**"):
                            st.write(f"**AI 藍海市場診斷分析**：{kv.get('reason')}")
                            
                    st.divider()
                    
                    # --- 💰 功能三：主流電商實時行情與財務定價策略 ---
                    st.header("💰 功能三：主流電商實時行情與財務定價策略")
                    prices = [item.get("price") for item in result.get('competitor_prices', []) if isinstance(item.get("price"), (int, float))]
                    avg_p = sum(prices) / len(prices) if prices else 0
                    
                    col_p1, col_p2 = st.columns([1, 1])
                    with col_p1:
                        st.subheader("🛒 實時台灣市場現況")
                        for item in result.get('competitor_prices', []):
                            st.write(f"* **{item.get('platform')}**： NT$ {item.get('price', 0):,} 元 — *{item.get('title')[:18]}...*")
                        if avg_p > 0:
                            st.info(f"💡 當前全台電商平均行情價：**NT$ {round(avg_p):,} 元**")
                            
                    with col_p2:
                        st.subheader("📋 機器人建議定價明細 (內含5%發票稅)")
                        market_suggested = round(avg_p * 0.95) if avg_p > 0 else 0
                        if market_suggested > 0:
                            st.markdown(f"""
                            | 定價策略 | 建議零售價 (含稅) | 開立發票基礎 (銷售額) | 應繳納之 5% 營業稅 |
                            | :--- | :--- | :--- | :--- |
                            | **策略 A：市場均價 95%** | **NT$ {market_suggested:,} 元** | NT$ {round(market_suggested/1.05):,} 元 | NT$ {market_suggested - round(market_suggested/1.05):,} 元 |
                            """)
                            
                        if estimated_cost > 0:
                            cost_suggested = round(estimated_cost * 1.20 * 1.05)
                            sales_amount = round(cost_suggested / 1.05)
                            tax_amount = cost_suggested - sales_amount
                            st.markdown(f"""
                            | 定價策略 | 建議零售價 (含稅) | 開立發票基礎 (銷售額) | 應繳納之 5% 營業稅 |
                            | :--- | :--- | :--- | :--- |
                            | **策略 B：成本 + 20% 利潤** | **NT$ {cost_suggested:,} 元** | NT$ {sales_amount:,} 元 | NT$ {tax_amount:,} 元 |
                            """)
                            
                    st.warning(f"💡 **AI 實戰定價與操盤方針**：\n{result.get('pricing_strategy')}")
                    
                except Exception as parse_error:
                    st.error("🛑 解析失敗。建議換個精準商品詞再試一次！")
