import streamlit as st
import pandas as pd
import yfinance as yf

# --- Page Config ---
st.set_page_config(page_title="MegaBull | Your Trading Playground", layout="wide")

# --- Initialize Session State (In-Memory Database) ---
if 'balance' not in st.session_state:
    st.session_state['balance'] = 444629.00 # Starting virtual cash
if 'positions' not in st.session_state:
    st.session_state['positions'] = {} # Format: {'TICKER': {'qty': int, 'avg': float}}

# --- Helper Function: Get Live Price ---
def get_live_price(ticker):
    try:
        # yfinance uses .NS for Indian National Stock Exchange
        stock = yf.Ticker(f"{ticker}.NS")
        return round(stock.history(period="1d")['Close'].iloc[-1], 2)
    except:
        return None

# --- Sidebar: Watchlist & Orders ---
with st.sidebar:
    st.title("Search Instrument")
    
    # Watchlist Example
    watchlist = ["SAIL", "INFY", "MRPL", "HYUNDAI", "LICI", "AXISBANK", "CANBK"]
    st.write("### Watchlist")
    for symbol in watchlist:
        price = get_live_price(symbol)
        st.write(f"**{symbol}** : ₹{price if price else 'N/A'}")
        
    st.divider()
    
    # Order Execution Form
    st.write("### Place Order")
    ticker = st.text_input("Ticker Symbol (e.g., SAIL, INFY)", "").upper()
    action = st.selectbox("Action", ["Buy", "Sell"])
    qty = st.number_input("Quantity", min_value=1, step=1)
    
    if st.button("Execute Order"):
        if ticker:
            ltp = get_live_price(ticker)
            if ltp:
                total_cost = ltp * qty
                
                if action == "Buy":
                    if st.session_state['balance'] >= total_cost:
                        st.session_state['balance'] -= total_cost
                        pos = st.session_state['positions'].get(ticker, {'qty': 0, 'avg': 0.0})
                        # Calculate new average
                        old_total = pos['qty'] * pos['avg']
                        pos['avg'] = (old_total + total_cost) / (pos['qty'] + qty)
                        pos['qty'] += qty
                        st.session_state['positions'][ticker] = pos
                        st.success(f"Bought {qty} shares of {ticker} at ₹{ltp}")
                    else:
                        st.error("Insufficient Funds!")
                        
                elif action == "Sell":
                    pos = st.session_state['positions'].get(ticker)
                    if pos and pos['qty'] >= qty:
                        st.session_state['balance'] += total_cost
                        pos['qty'] -= qty
                        if pos['qty'] == 0:
                            del st.session_state['positions'][ticker]
                        st.success(f"Sold {qty} shares of {ticker} at ₹{ltp}")
                    else:
                        st.error("Insufficient shares in portfolio!")
            else:
                st.error("Invalid Ticker or Data Unavailable.")

# --- Main Canvas: Positions Dashboard ---
st.title("MegaBull | Your Trading Playground")

# Top Metrics Bar
col1, col2 = st.columns(2)
col1.metric("Available Virtual Money", f"₹ {st.session_state['balance']:,.2f}")

st.subheader("Positions")

# Calculate metrics for the Positions Table
if st.session_state['positions']:
    table_data = []
    total_pnl = 0.0
    
    for sym, data in st.session_state['positions'].items():
        ltp = get_live_price(sym)
        if ltp:
            pnl = (ltp - data['avg']) * data['qty']
            total_pnl += pnl
            change_pct = ((ltp - data['avg']) / data['avg']) * 100 if data['avg'] > 0 else 0
            
            table_data.append({
                "PRODUCT": "MIS",
                "INSTRUMENT": sym,
                "QTY": data['qty'],
                "AVG": round(data['avg'], 2),
                "LTP": ltp,
                "P&L": round(pnl, 2),
                "CHG %": f"{round(change_pct, 2)}%"
            })
            
    col2.metric("Total P&L", f"₹ {total_pnl:,.2f}", delta=round(total_pnl, 2))
    
    # Display as DataFrame
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    col2.metric("Total P&L", "₹ 0.00")
    st.info("No open positions.")
