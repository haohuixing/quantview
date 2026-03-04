#### import items 
# Made by other people 
import streamlit
import yfinance
import webbrowser
import threading 
from streamlit_autorefresh import st_autorefresh
import pandas as pd

#Made by me
import toolkit
import classes 

################################### Load data from databases 



####################### MANGE CSS AND HTML ELEMENTS THAT STREAMLIT DOES WRONG BY DEFAULT 
with open("style.css") as f:
        streamlit.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


##################### The app itself (webpage and all frontend stuff) #######################
### Store in session state what webpage people are looking at
if "cover" not in streamlit.session_state:
    streamlit.session_state.cover = True
if "login" not in streamlit.session_state:
    streamlit.session_state.login = False
if "signup" not in streamlit.session_state:
    streamlit.session_state.signup = False 
if "lookup" not in streamlit.session_state:
    streamlit.session_state.lookup = False
if "home" not in streamlit.session_state:
    streamlit.session_state.home = False
if "alarms" not in streamlit.session_state:
    streamlit.session_state.alarms = False
    
    
### Store in session state data 
if "alarm_list" not in streamlit.session_state: ## This is not for webpage navigation, but for saving alarms. 
    streamlit.session_state.alarm_list = []
if "notif_queue" not in streamlit.session_state: ## This is not for webpage navigation, but for saving alarms that are raised right now. 
    streamlit.session_state.notif_queue = classes.Queue(max_size=10)
if "view_ticker" not in streamlit.session_state:
    streamlit.session_state.view_ticker = "AAPL"
if "watchlist" not in streamlit.session_state:
    streamlit.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT", "AMD", "GOOGL", "AMZN", "META", "NFLX"]
    


################## Background code that will always be running!
# Trigger refresh every 5 seconds
st_autorefresh(interval=5000, key="datarefresh")
for alarm in streamlit.session_state.alarm_list:
    triggered, current_val = alarm.check_alarm()
    if triggered:
        alarm.raise_alarm(current_val) # Plays sound/shows toast
        
        # ADD TO QUEUE
        notif_data = {
            "stock": alarm.get_stock(),
            "variable": alarm.get_variable(),
            "value": current_val,
            "type": type(alarm).__name__,
            "time": pd.Timestamp.now().strftime("%H:%M:%S")
        }
        streamlit.session_state.notif_queue.enqueue(notif_data)
        
###### DIFFERNET WEBPAGES

# Cover page 
def cover_page():
    streamlit.set_page_config(
        page_title = "QuantView" 
    )
    streamlit.markdown("<h1 class = 'main-title'> QuantView </h1>", unsafe_allow_html = True) 
    col1, col2, col3, col4, col5, col6 = streamlit.columns([1, 1, 1, 1, 1, 1]) #extra columns for padding 
    
    
    with col3:
        if streamlit.button("Sign Up", use_container_width = True):
            streamlit.session_state.cover = False
            streamlit.session_state.signup = True
            streamlit.rerun()
    with col4:
        if streamlit.button("Log In", use_container_width = True):
            streamlit.session_state.cover = False
            streamlit.session_state.login = True
            streamlit.rerun()
        

# LOGIN PAGE 
def login_page():
    streamlit.set_page_config(
        page_title = "Login | QuantView"
    )
    streamlit.title("Log In")
    
    with streamlit.form("login_form"):
        username = streamlit.text_input("Username: ")
        password = streamlit.text_input("Password: ", type = "password")
        submitted = False 
        tosignup = False 
        toreturn = False 
        col1, col2, col3, col4 = streamlit.columns([1.5, 1.5, 1.5, 4]); #4th column is for padding/spacing 
        
        
        with col1:
            submitted = streamlit.form_submit_button("Enter", use_container_width = True)
        with col2:
            tosignup = streamlit.form_submit_button("Sign Up", use_container_width = True)
        with col3:
            toreturn = streamlit.form_submit_button("Return", use_container_width = True)
        if submitted:
            
            #### CREATE LOGIC FOR ACTUALLY FINDING AN ACCOUNT OKAY TY
            if username == "MARK SUCKERBURG" and password == "MUGNAR":
                streamlit.session_state.login = False
                streamlit.session_state.home = True
                streamlit.rerun()
            else:
                streamlit.error("INVALID USERNAME OR PASSWORD")
        elif tosignup:
            streamlit.session_state.login = False
            streamlit.session_state.signup = True
            streamlit.rerun()
        elif toreturn:
            streamlit.session_state.login = False
            streamlit.session_state.cover = True
            streamlit.rerun()
# Sign UP PAGE 
def signup_page():
    streamlit.set_page_config(
        page_title = "Sign Up | QuantView"
    )
    streamlit.title("Create Your Free Account")
    
    with streamlit.form("signup_form"):
        username = streamlit.text_input("Username: ")
        password = streamlit.text_input("Password: ", type = "password")
        recom = streamlit.text_input("Re-enter Password: ", type = "password")
        
        submitted = False 
        tologin = False 
        toreturn = False 
        col1, col2, col3, col4 = streamlit.columns([1.5, 1.5, 1.5, 3]);
        
        with col1:
            submitted = streamlit.form_submit_button("Make Account", use_container_width = True)
        with col2:
            tologin = streamlit.form_submit_button("Log In", use_container_width = True)
        with col3:
            toreturn = streamlit.form_submit_button("Return", use_container_width = True)
            
        if submitted:
            if password == recom:
                streamlit.session_state.signup = False
                streamlit.session_state.home = True
                
                
                ###### CREATE LOGIC FOR ADDING ACCOUNT TO DATABASE!!!!
                
                
                
                
                streamlit.rerun()
            else:
                streamlit.error("Passwords do not match!")      
        elif tologin:
            streamlit.session_state.signup = False
            streamlit.session_state.login = True
            streamlit.rerun()
        elif toreturn:
            streamlit.session_state.signup = False
            streamlit.session_state.cover = True
            streamlit.rerun()
    
# Look at stock charts 
def stock_lookup():
    streamlit.set_page_config(page_title="Stocks | QuantView", layout="wide")
    # --- TOP NAV ---
    col_back, col_title = streamlit.columns([1, 8])
    with col_back:
        if streamlit.button("← Home"):
            streamlit.session_state.lookup = False
            streamlit.session_state.home = True
            streamlit.rerun()
    with col_title:
        streamlit.markdown(f"<h1 style='margin-top:-10px;'>QuantView - {streamlit.session_state.view_ticker}</h1>", unsafe_allow_html=True)

    # --- 1. MAIN GRAPH SECTION ---
    current_stock = yfinance.Ticker(streamlit.session_state.view_ticker)
    
    hist = current_stock.history(period="5y")
    
    if not hist.empty:
        streamlit.line_chart(hist['Close'], height=350, color="#2563EB")
    else:
        streamlit.error("Could not load chart data.")

    # --- 2. METRICS BAR ---
    # Fetching detailed info for the single viewed stock
    s_info = current_stock.info
    
    # Helper to format data safely
    def get_val(key, fmt="{:.2f}"):
        v = s_info.get(key)
        return fmt.format(v) if v is not None else "N/A"

    # Row 1 of metrics
    m1, m2, m3, m4, m5, m6, m7, m8, m9 = streamlit.columns([1,1,1,1,1,1,1,1,1.5])
    
    m1.metric("Price", f"${get_val('currentPrice')}")
    m2.metric("Volume", f"{s_info.get('volume', 0):,}")
    m3.metric("Prev Close", f"${get_val('previousClose')}")
    
    # Calculate % Delta manually for accuracy
    try:
        delta = ((s_info['currentPrice'] - s_info['previousClose']) / s_info['previousClose']) * 100
        m4.metric("% Δ Price", f"{delta:.2f}%", delta_color="normal")
    except: m4.metric("% Δ Price", "N/A")

    m5.metric("Alpha (1y)", f"{toolkit.calcAlpha(current_stock):.2f}") 
    m6.metric("Beta", get_val('beta'))
    m7.metric("EPS", get_val('trailingEps'))
    m8.metric("PE Ratio", get_val('trailingPE'))
    
    with m9:
        streamlit.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        if streamlit.button("+ Add to Watchlist", use_container_width=True):
            if streamlit.session_state.view_ticker not in streamlit.session_state.watchlist:
                streamlit.session_state.watchlist.append(streamlit.session_state.view_ticker)
                streamlit.toast(f"Added {streamlit.session_state.view_ticker} to Watchlist!")

    streamlit.markdown("---")

    # --- 3. SEARCH BAR ---
    search_query = streamlit.text_input("🔍 Search Stock Ticker (e.g. NVDA, BTC-USD)", "").upper()
    if search_query:
        if streamlit.button(f"Load {search_query}"):
            streamlit.session_state.view_ticker = search_query
            streamlit.rerun()

    # --- 4. TOP 50 MARKET LIST ---
    streamlit.markdown("### Market Leaders - Largest Market Capitalization")
    
    # 1. UI for Sorting
    s1, s2 = streamlit.columns([2, 2])
    with s1:
        # Added "Market Cap" and set it as the default (index 4)
        m_sort_on = streamlit.selectbox(
            "Sort Market By", 
            ["Ticker", "Price", "Volume", "% Change", "Market Cap"], 
            index=4, 
            label_visibility="collapsed"
        )
    with s2:
        # Set "Descending" as the default (index 1)
        m_direction = streamlit.selectbox(
            "Market Order", 
            ["Ascending", "Descending"], 
            index=1, 
            label_visibility="collapsed"
        )
    m_reverse = True if m_direction == "Descending" else False

    # Define top tickers
    top_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "LLY", 
                   "V", "JPM", "AVGO", "MA", "HD", "PG", "COST", "ORCL", "ADBE", "NFLX",
                   "AMD", "PEP", "BAC", "CRM", "CVX", "WMT", "KO", "TMO", "ABT", "DIS",
                   "MCD", "CSCO", "INTC", "PFE", "VZ", "TMUS", "NKE", "INTU", "AMAT", "UPS"]

    @streamlit.cache_data(ttl=600) # Cache for 10 mins since Market Cap doesn't change every second
    def get_extended_market_data(tickers):
        # Batch download prices
        price_data = yfinance.download(tickers, period="2d", interval="1d", progress=False)
        
        # Fetch Market Cap for each ticker
        market_caps = {}
        for t in tickers:
            try:
                # We use Ticker(t).info for marketCap
                market_caps[t] = yfinance.Ticker(t).info.get('marketCap', 0)
            except:
                market_caps[t] = 0
        return price_data, market_caps

    try:
        market_raw, caps_dict = get_extended_market_data(top_tickers)
        
        # 2. Process data into a list for sorting
        market_list = []
        for ticker in top_tickers:
            try:
                current_p = float(market_raw['Close'][ticker].iloc[-1])
                prev_p = float(market_raw['Close'][ticker].iloc[-2])
                vol = float(market_raw['Volume'][ticker].iloc[-1])
                change = ((current_p - prev_p) / prev_p) * 100
                m_cap = caps_dict.get(ticker, 0)
                
                market_list.append({
                    "Ticker": ticker,
                    "Price": current_p,
                    "Volume": vol,
                    "% Change": change,
                    "Market Cap": m_cap
                })
            except:
                continue 

        # 3. USE YOUR MERGE SORT!
        sorted_market = toolkit.merge_sort(market_list, key=m_sort_on, reverse=m_reverse)

        # 4. Render Table (Added Market Cap column)
        streamlit.markdown("<br>", unsafe_allow_html=True)
        h1, h2, h3, h4, h5, h6 = streamlit.columns([1, 1, 1, 1, 1, 1])
        h1.write("**Ticker**")
        h2.write("**Price**")
        h3.write("**% Change**")
        h4.write("**Market Cap**")
        h5.write("**Volume**")
        h6.write("**Action**")

        for item in sorted_market:
            color = "#00FF41" if item["% Change"] >= 0 else "#FF3131"
            
            # Format Market Cap (e.g., 3.1T, 500.2B)
            cap = item["Market Cap"]
            if cap >= 1e12: cap_str = f"${cap/1e12:.2f}T"
            elif cap >= 1e9: cap_str = f"${cap/1e9:.1f}B"
            else: cap_str = f"${cap/1e6:.1f}M"

            r1, r2, r3, r4, r5, r6 = streamlit.columns([1, 1, 1, 1, 1, 1])
            r1.markdown(f"**{item['Ticker']}**")
            r2.write(f"${item['Price']:.2f}")
            r3.markdown(f"<span style='color:{color};'>{item['% Change']:+.2f}%</span>", unsafe_allow_html=True)
            r4.write(cap_str)
            r5.write(f"{item['Volume']/1e6:.1f}M")
            
            if r6.button("View", key=f"view_mkt_{item['Ticker']}", use_container_width=True):
                streamlit.session_state.view_ticker = item['Ticker']
                streamlit.rerun()

    except Exception as e:
        streamlit.error(f"Error loading market leaders: {e}")
 
 
# Look at the alarmpage
def alarmpage():
    streamlit.set_page_config(page_title="Alarms | QuantView", layout="wide")

    # Navigation back to home
    if streamlit.button("Back to Dashboard"):
        streamlit.session_state.alarms = False
        streamlit.session_state.home = True
        streamlit.rerun()

    streamlit.markdown("<h1 style='text-align: center;'>Customize Alarms</h1>", unsafe_allow_html=True)
    
    # --- SECTION: ADD AN ALARM ---
    streamlit.markdown("<h3 style='text-align: center;'>Add an Alarm</h3>", unsafe_allow_html=True)
    
    # Matching your layout drawing (6 columns)
    col_size, col_stock, col_var, col_op, col_val, col_btn = streamlit.columns([1.5, 1.5, 2, 1, 1.5, 1.5])
    
    with col_size:
        size_choice = streamlit.selectbox("Size", ["Small", "Medium", "Loud"])
    with col_stock:
        stock_input = streamlit.text_input("Stock", placeholder="AAPL")
    with col_var:
        var_choice = streamlit.selectbox("Indicator", ["Price", "Volume", "% DELTA Price", "Alpha", "Beta", "EPS", "PE Ratio"])
    with col_op:
        op_choice = streamlit.selectbox("Operator", [">", "<", ">=", "<=", "==", "!="])
    with col_val:
        val_input = streamlit.text_input("Target Value", placeholder="200.0")
    with col_btn:
        streamlit.markdown("<br>", unsafe_allow_html=True) # Align button
        if streamlit.button("Add Alarm", use_container_width=True):
            # 1. Instantiate the correct Subclass
            if size_choice == "Small":
                temp_alarm = classes.SmallAlarm()
            elif size_choice == "Medium":
                temp_alarm = classes.MediumAlarm()
            else:
                temp_alarm = classes.LoudAlarm()
            
            # 2. Validation using your existing setters
            # Setters return True if valid, False + st.error if invalid
            success = [
                temp_alarm.set_stock(stock_input),
                temp_alarm.set_variable(var_choice),
                temp_alarm.set_operator(op_choice),
                temp_alarm.set_target(val_input)
            ]
            
            # 3. Only add if ALL setters passed
            if all(success):
                streamlit.session_state.alarm_list.append(temp_alarm)
                streamlit.success(f"Added {size_choice} Alarm for {stock_input}!")
                streamlit.rerun()

    streamlit.markdown("---")

    # --- SECTION: VIEW YOUR ALARMS ---
    streamlit.markdown("<h3 style='text-align: center;'>View Your Alarms</h3>", unsafe_allow_html=True)
    
    if not streamlit.session_state.alarm_list:
        streamlit.info("No alarms set. Create one above!")
    else:
        for index, alarm in enumerate(reversed(streamlit.session_state.alarm_list)):
            with streamlit.container():
                real_index = len(streamlit.session_state.alarm_list) - 1 - index
                
                # We use 3 columns now: Info, Reactivate, Remove
                c1, c2, c3 = streamlit.columns([6, 2, 2])
                
                with c1:
                    alarm_type = type(alarm).__name__
                    color = "#2563EB"
                    if alarm_type == "MediumAlarm": color = "#F59E0B"
                    elif alarm_type == "LoudAlarm": color = "#EF4444"

                    # Add a "(TRIGGERED)" tag if the alarm has fired
                    status_text = ""
                    if alarm.is_fired():
                        status_text = f" <span style='color: {color}; font-weight: bold;'>[TRIGGERED]</span>"

                    streamlit.markdown(f"""
                    <div style='background: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; border-left: 5px solid {color};'>
                        <strong style='color: {color};'>{alarm_type}</strong> | 
                        Stock: <b>{alarm.get_stock()}</b> | 
                        Condition: <b>{alarm.get_variable()} {alarm.get_operator()} {alarm.get_target()}</b>{status_text}
                    </div>
                    """, unsafe_allow_html=True)
                
                with c2:
                    streamlit.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    # ONLY show the Reactivate button if the alarm is currently fired
                    if alarm.is_fired():
                        if streamlit.button("Reactivate", key=f"re_{real_index}", use_container_width=True):
                            alarm.reactivate()
                            streamlit.success("Alarm Ready!")
                            streamlit.rerun()
                    else:
                        # Display a "Watching" label if not fired yet
                        streamlit.markdown("<p style='text-align:center; color:#8B949E; margin-top:15px;'>Monitoring...</p>", unsafe_allow_html=True)

                with c3:
                    streamlit.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    if streamlit.button("Remove", key=f"del_{real_index}", use_container_width=True):
                        streamlit.session_state.alarm_list.pop(real_index)
                        streamlit.rerun()
                
                streamlit.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
# Look at homescreen     
def homescreen():

    streamlit.set_page_config(page_title="Dashboard | QuantView", layout="wide")
    streamlit.markdown("<div class='dashboard-title'>QuantView Dashboard</div>", unsafe_allow_html=True)

    col_left, col_right = streamlit.columns([1.2, 1], gap="large")

    # Define Bright Colors to match the theme
    COLOR_GREEN = "#00FF41" # Matrix Green
    COLOR_RED = "#FF3131"   # Neon Red

    # --- LEFT COLUMN: Market Watchlist ---
    # --- LEFT COLUMN: Market Watchlist ---
    with col_left:
        streamlit.markdown("### Market Watchlist")

        # 1. UI for Sorting - Added "Volume" to the list
        s1, s2 = streamlit.columns(2)
        sort_on = s1.selectbox("Sort By", ["Ticker", "Price", "Change", "Volume"], label_visibility="collapsed")
        direction = s2.selectbox("Order", ["Ascending", "Descending"], label_visibility="collapsed")
        is_reverse = True if direction == "Descending" else False

        tickers = streamlit.session_state.watchlist

        if not tickers:
            streamlit.info("Your watchlist is empty.")
        else:
            try:
                # 2. Fetch data (yfinance downloads Close and Volume by default)
                data = yfinance.download(tickers, period="2d", interval="1d", progress=False)
                
                # 3. Build a list of data objects
                watchlist_data = []
                for ticker in tickers:
                    # Logic to handle single vs multiple stocks in yfinance download
                    if len(tickers) > 1:
                        close_series = data['Close'][ticker].dropna()
                        vol_series = data['Volume'][ticker].dropna()
                    else:
                        close_series = data['Close'].dropna()
                        vol_series = data['Volume'].dropna()
                    
                    if not close_series.empty and len(close_series) >= 2:
                        curr = float(close_series.iloc[-1])
                        prev = float(close_series.iloc[-2])
                        change = ((curr - prev) / prev) * 100
                        vol = float(vol_series.iloc[-1]) # Fetching Volume
                        
                        watchlist_data.append({
                            "Ticker": ticker,
                            "Price": curr,
                            "Change": change,
                            "Volume": vol
                        })
                    else:
                        watchlist_data.append({"Ticker": ticker, "Price": 0.0, "Change": 0.0, "Volume": 0})

                # 4. Use your Merge Sort from toolkit.py
                sorted_watchlist = toolkit.merge_sort(watchlist_data, key=sort_on, reverse=is_reverse)

                # 5. Render the table
                streamlit.markdown("<br>", unsafe_allow_html=True)
                # Adjusted column ratios to fit 4 data columns + 1 button column
                h1, h2, h3, h4, h5 = streamlit.columns([1, 1, 1, 1, 0.5])
                h1.write("**Ticker**")
                h2.write("**Price**")
                h3.write("**Change**")
                h4.write("**Volume**")
                h5.write("")

                for item in sorted_watchlist:
                    r1, r2, r3, r4, r5 = streamlit.columns([1, 1, 1, 1, 0.5])
                    ticker = item["Ticker"]
                    
                    color = COLOR_GREEN if item["Change"] >= 0 else COLOR_RED
                    sign = "+" if item["Change"] > 0 else ""

                    # Formatting Volume to be readable (e.g., 1.2M)
                    vol_display = f"{item['Volume']/1e6:.1f}M" if item['Volume'] >= 1e6 else f"{item['Volume']:,.0f}"

                    r1.markdown(f"**{ticker}**")
                    r2.write(f"${item['Price']:,.2f}")
                    r3.markdown(f"<span style='color:{color};'>{sign}{item['Change']:.2f}%</span>", unsafe_allow_html=True)
                    r4.write(vol_display)
                    
                    if r5.button("🗑️", key=f"del_watch_{ticker}"):
                        streamlit.session_state.watchlist.remove(ticker)
                        streamlit.rerun()

            except Exception as e:
                streamlit.error(f"Error loading watchlist: {e}")
    # --- RIGHT COLUMN: S&P 500 Performance ---
    with col_right:
        streamlit.markdown("### S&P 500 Performance")
        sp_data = yfinance.download("^GSPC", period="1y", interval="1d", progress=False)
        
        if not sp_data.empty:
            chart_data = sp_data['Close']
            column_count = len(chart_data.columns) if hasattr(chart_data, 'columns') else 1
            chart_colors = ["#2563EB"] * column_count
            streamlit.line_chart(chart_data, height=280, color=chart_colors)
            
            # Calculate % Change for the Header
            try:
                current_sp = float(chart_data.iloc[-1])
                prev_sp = float(chart_data.iloc[-2])
                sp_change = ((current_sp - prev_sp) / prev_sp) * 100
                
                sp_color = COLOR_GREEN if sp_change >= 0 else COLOR_RED
                sp_sign = "+" if sp_change >= 0 else ""

                # Display Price (White) and Change (Colored)
                streamlit.markdown(
                    f"""
                    <div class='price-text'>
                        Current S&P 500: 
                        <span style='color: white !important; font-weight: 700;'>${current_sp:,.2f}</span>
                        <span style='color: {sp_color}; font-weight: 700; margin-left: 12px;'>
                            ({sp_sign}{sp_change:.2f}%)
                        </span>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            except:
                streamlit.write("Updating Index...")

        streamlit.markdown("<br>", unsafe_allow_html=True)
        if streamlit.button("View Stocks", key="home_view_btn", use_container_width=True):
            streamlit.session_state.home = False
            streamlit.session_state.lookup = True
            streamlit.rerun()

        if streamlit.button("Customize Alarms", key="home_alarm_btn", use_container_width=True):
            streamlit.session_state.home = False
            streamlit.session_state.alarms = True # Updated key
            streamlit.rerun()
            
            
    # BOTTOM SECTION: Notifications (The Queue)
    streamlit.markdown("---")
    streamlit.markdown("<h3 style='text-align: center;'>Recent Notifications</h3>", unsafe_allow_html=True)
    
    q = streamlit.session_state.notif_queue
    
    # We use a container to keep everything grouped
    with streamlit.container():
        if q.isEmpty():
            streamlit.markdown("<p style='text-align: center; color: #8B949E;'>No recent notifications.</p>", unsafe_allow_html=True)
        else:
            # Container for the 'box' look
            # Note: No indentation inside the f-string for the first line of HTML!
            items = q.get_all_items()
            
            for item in items:
                # Determine color based on severity
                color = "#2563EB" # Default Blue
                if item['type'] == "MediumAlarm": color = "#F59E0B" # Orange
                if item['type'] == "LoudAlarm": color = "#EF4444"   # Red
                
                # Render each notification as a clean block
                # IMPORTANT: The <div> must start at the very edge of the string
                streamlit.markdown(f"""
                <div style='background: #161B22; border: 1px solid #30363D; border-left: 5px solid {color}; border-radius: 8px; padding: 12px; margin-bottom: 10px;'>
                    <span style='color: #8B949E; font-size: 0.85rem;'>[{item['time']}]</span> 
                    <strong style='color: {color}; font-size: 1.1rem; margin-left: 10px;'>{item['stock']}</strong> 
                    <span style='color: #E6EDF3; margin-left: 5px;'>{item['variable']} triggered at <b>{item['value']:.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)

            if streamlit.button("Clear Notification History", use_container_width=True):
                q.clear()
                streamlit.rerun()  
# MANAGE DIFFERENT WEBPAGES 
if streamlit.session_state.cover:
   cover_page()
elif streamlit.session_state.login:
   login_page()
elif streamlit.session_state.signup:
   signup_page()
elif streamlit.session_state.lookup:
   stock_lookup()
elif streamlit.session_state.home:
    homescreen()
elif streamlit.session_state.alarms:
    alarmpage()
else:
    homescreen()

    
