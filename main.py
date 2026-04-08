#### This is main.py, the main file for my IA
# Contains:
# - The GUI of the IA 
# - The entire underlying system of the code (where all the code interacts with each other, the backbone)
# - The various webpages and such  


############### import items 
# These are libraries made by other people 
import streamlit
import yfinance
from streamlit_autorefresh import st_autorefresh
import pandas as pd

#Made by me, for this IA 
import toolkit
import classes 
import database

 
streamlit.markdown('<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300..700&display=swap" rel="stylesheet">', unsafe_allow_html =  True) # Import a font from google fonts 
with open("style.css") as f: # Open and read from a file. This imports CSS code from "style.css", to be used in this project 
        streamlit.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


##################### The app itself (webpage and all frontend stuff) #######################
### Store in session state what webpage the user islooking at
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
    
    
### Data to be stored in session state
if "current_user" not in streamlit.session_state: # Stores the username of the current user 
    streamlit.session_state.current_user = None
if "alarm_list" not in streamlit.session_state: # Stores the alarms that the user has 
    streamlit.session_state.alarm_list = []
if "notif_queue" not in streamlit.session_state: # Stores the notifications that the user has 
    streamlit.session_state.notif_queue = classes.Queue(max_size=10) # contained in a queue that has max 10 items (this way notification list isn't too long) 
if "view_ticker" not in streamlit.session_state: # What stock the user is looking at in the webpage "view stocks"
    streamlit.session_state.view_ticker = "AAPL"
if "watchlist" not in streamlit.session_state: # List of stocks the user has on the webpage
    streamlit.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT", "AMD", "GOOGL", "AMZN", "META", "NFLX"]
    


################## Background code that will always be running!
# Refresh the webpage, to check alarms and update stock numbers every 5 seconds
st_autorefresh(interval=5000, key="datarefresh")

# Check for any alarms that need to be raised 
for alarm in streamlit.session_state.alarm_list:
    
    # This function returns two values: triggered (if the alarm has been triggered), and the value reached when the alarm has been triggered
    triggered, current_val = alarm.check_alarm() 
    
    if triggered:
        alarm.raise_alarm(current_val) # raise the alarm 
        
        if streamlit.session_state.current_user:
            database.update_alarm_fired_status(  # Save the raised alarm to database
                streamlit.session_state.current_user,
                alarm.get_stock(),
                alarm.get_variable(),
                alarm.get_target(),
                True 
            )
            
            # Save Notification
            notif_data = {
                "stock": alarm.get_stock(), "variable": alarm.get_variable(),
                "value": current_val, "type": type(alarm).__name__,
                "time": pd.Timestamp.now().strftime("%H:%M:%S")
            }
            
            # Save the notification to database
            database.save_notification(streamlit.session_state.current_user, notif_data)
            streamlit.session_state.notif_queue.enqueue(notif_data)
        
################### DIFFERNET WEBPAGES

### Cover page (The first page users see)
def cover_page():
    streamlit.set_page_config(
        page_title = "QuantView" 
    )
    streamlit.markdown("<h1 class = 'main-title'> QuantView </h1>", unsafe_allow_html = True) 
    col1, col2, col3, col4, col5, col6 = streamlit.columns([1, 1, 1, 1, 1, 1]) #extra columns for padding 
    
    # Sign up button 
    with col3:
        if streamlit.button("Sign Up", use_container_width = True):
            streamlit.session_state.cover = False
            streamlit.session_state.signup = True
            streamlit.rerun()
    # Log in button
    with col4:
        if streamlit.button("Log In", use_container_width = True):
            streamlit.session_state.cover = False
            streamlit.session_state.login = True
            streamlit.rerun()
        

### LOGIN PAGE 
def login_page():
    streamlit.set_page_config(
        page_title = "Login | QuantView"
    )
    streamlit.title("Log In")
    
    ## login menu 
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
            # If they can log into their account
            if database.login(username, password):
                streamlit.session_state.current_user = username
                # LOAD USER DATA
                streamlit.session_state.watchlist = database.get_watchlist(username)
                streamlit.session_state.alarm_list = database.load_alarms(username)
                
                # Load recent notifications into Queue
                past_notifs = database.load_notifications(username)
                streamlit.session_state.notif_queue.clear()
                for n in reversed(past_notifs): # Rebuild queue from oldest to newest
                    streamlit.session_state.notif_queue.enqueue({
                        "stock": n['stock'], "variable": n['variable'], "value": n['value'], 
                        "type": n['alarm_type'], "time": "Past Alert"
                    })
                    
                # Switch webpage to the homescreen 
                streamlit.session_state.login = False
                streamlit.session_state.home = True
                streamlit.rerun()
            else: # If they can't log in thats username or password wrong 
                streamlit.error("INVALID USERNAME OR PASSWORD")
        elif tosignup:
            streamlit.session_state.login = False
            streamlit.session_state.signup = True
            streamlit.rerun()
        elif toreturn:
            streamlit.session_state.login = False
            streamlit.session_state.cover = True
            streamlit.rerun()
### Sign UP PAGE 
def signup_page():
    streamlit.set_page_config(
        page_title = "Sign Up | QuantView"
    )
    streamlit.title("Create Your Free Account")
    
    with streamlit.form("signup_form"):
        username = streamlit.text_input("Username: ")
        password = streamlit.text_input("Password (At Least 6 Characters): ", type = "password")
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
            if password == recom: # If the password they typed is same as the "confirm password"
                if database.signup(username, password): # If they can sign up 
                    streamlit.session_state.current_user = username 
                    streamlit.session_state.watchlist = [] # Fresh start for new user
                    streamlit.session_state.alarm_list = [] # Fresh start
                    
                    streamlit.session_state.signup = False
                    streamlit.session_state.home = True
                    streamlit.rerun()
                else:
                    streamlit.error("Password not over 6 characters or Username already taken!") # If they can't signup somehow
                
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
    
### Look at stock charts and search for stocks 
def stock_lookup():
    streamlit.set_page_config(page_title="Stocks | QuantView", layout="wide")
    # --- TOP NAV ---
    col_back, col_title = streamlit.columns([1, 8])
    with col_back:
        if streamlit.button("← Home"): # Back button 
            streamlit.session_state.lookup = False
            streamlit.session_state.home = True
            streamlit.rerun()
    with col_title:
        streamlit.markdown(f"<h1 style='margin-top:-10px;'>QuantView - {streamlit.session_state.view_ticker}</h1>", unsafe_allow_html=True)

    # The graph 
    current_stock = yfinance.Ticker(streamlit.session_state.view_ticker)
    
    hist = current_stock.history(period="5y") 
    
    if not hist.empty: # Load chart for closing prices in the past 5 years 
        streamlit.line_chart(hist['Close'], height=350, color="#2563EB")
    else:
        streamlit.error("Could not load chart data.")


    # Fetching detailed info for the stock the user is viewing right now
    s_info = current_stock.info
    
    # Helper function to format data
    def get_val(key, fmt="{:.2f}"):
        v = s_info.get(key)
        return fmt.format(v) if v is not None else "N/A"

    # Row 1 of metrics
    m1, m2, m3, m4, m5, m6, m7, m8, m9 = streamlit.columns([1,1,1,1,1,1,1,1,1.5])
    
    m1.metric("Price", f"${get_val('currentPrice')}")
    m2.metric("Volume", f"{s_info.get('volume', 0):,}")
    m3.metric("Prev Close", f"${get_val('previousClose')}")
    
    # Calculate % Delta (percent change from last time) 
    try:
        delta = ((s_info['currentPrice'] - s_info['previousClose']) / s_info['previousClose']) * 100
        m4.metric("% Δ Price", f"{delta:.2f}%", delta_color="normal")
    except: m4.metric("% Δ Price", "N/A") # to avoid division by zero error 
    
    # Various either metrics/indicators
    m5.metric("Alpha (1y)", f"{toolkit.calcAlpha(current_stock):.2f}") 
    m6.metric("Beta", get_val('beta'))
    m7.metric("EPS", get_val('trailingEps'))
    m8.metric("PE Ratio", get_val('trailingPE'))
    
    with m9: # Add the stock to the watchlist button 
        streamlit.markdown("<div style='height:25px;'></div>", unsafe_allow_html=True)
        if streamlit.button("+ Add to Watchlist", use_container_width=True):
            streamlit.session_state.view_ticker = streamlit.session_state.view_ticker.upper()
            if streamlit.session_state.view_ticker.upper() not in streamlit.session_state.watchlist:
                streamlit.session_state.watchlist.append(streamlit.session_state.view_ticker)
                if streamlit.session_state.current_user:
                    database.add_watchlist(streamlit.session_state.current_user, streamlit.session_state.view_ticker) # add it to database as well
                streamlit.toast(f"Added {streamlit.session_state.view_ticker} to Watchlist!")

    streamlit.markdown("---")

    # Search Bar
    search_query = streamlit.text_input("Search Stock Ticker (e.g. NVDA, BTC-USD)", "").upper()
    if search_query:
        if streamlit.button(f"Load {search_query}"):
            streamlit.session_state.view_ticker = search_query
            streamlit.rerun()

    # List showing top 50 stocks by market cap 
    streamlit.markdown("### Market Leaders - Largest Market Capitalization")
    
    # Sorting UI 
    s1, s2 = streamlit.columns([2, 2])
    with s1:
        # Select box for what indicator to sort 
        m_sort_on = streamlit.selectbox(
            "Sort Market By", 
            ["Ticker", "Price", "Volume", "% Change", "Market Cap"], 
            index=4, # Default is market cap
            label_visibility="collapsed"
        )
    with s2:
        # Select descending or ascending for sorting 
        m_direction = streamlit.selectbox(
            "Market Order", 
            ["Ascending", "Descending"], 
            index=1, # Descending set as the default (index 1)
            label_visibility="collapsed"
        )
    m_reverse = True if m_direction == "Descending" else False

    # Define top tickers
    top_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "BRK-B", "UNH", "LLY", 
                   "V", "JPM", "AVGO", "MA", "HD", "PG", "COST", "ORCL", "ADBE", "NFLX",
                   "AMD", "PEP", "BAC", "CRM", "CVX", "WMT", "KO", "TMO", "ABT", "DIS",
                   "MCD", "CSCO", "INTC", "PFE", "VZ", "TMUS", "NKE", "INTU", "AMAT", "UPS"] # List of the biggest companies by market cap right now (hardcoded because this is unlikely to change in a long time)

    @streamlit.cache_data(ttl=600) # Cache for 10 mins since Market Cap doesn't significantly change every second
    def get_extended_market_data(tickers):
        # Download most of the data 
        price_data = yfinance.download(tickers, period="2d", interval="1d", progress=False)
        
        # Fetch Market Cap data, which doesn't come with the "most other data", for each ticker
        market_caps = {}
        for t in tickers:
            try:
                # We use Ticker(t).info for marketCap
                market_caps[t] = yfinance.Ticker(t).info.get('marketCap', 0)
            except:
                market_caps[t] = 0
        return price_data, market_caps

    try:
        market_raw, caps_dict = get_extended_market_data(top_tickers) # Get market data, get market caps 
        
        # 2. Process data into a list for sorting
        market_list = []
        for ticker in top_tickers:
            try:
                current_p = float(market_raw['Close'][ticker].iloc[-1]) # current price 
                prev_p = float(market_raw['Close'][ticker].iloc[-2]) # day before today price 
                vol = float(market_raw['Volume'][ticker].iloc[-1]) # Volume
                change = ((current_p - prev_p) / prev_p) * 100 # Change in price 
                m_cap = caps_dict.get(ticker, 0) # market cap 
                
                market_list.append({ # create a dictionary (type of hashmap) which assigns a variable to each indicator 
                    "Ticker": ticker,
                    "Price": current_p,
                    "Volume": vol,
                    "% Change": change,
                    "Market Cap": m_cap
                })
            except:
                continue 
        # Merge sort 
        sorted_market = toolkit.merge_sort(market_list, key=m_sort_on, reverse=m_reverse)

        ### Make the table 
        streamlit.markdown("<br>", unsafe_allow_html=True)
        h1, h2, h3, h4, h5, h6 = streamlit.columns([1, 1, 1, 1, 1, 1])
        h1.write("**Ticker**")
        h2.write("**Price**")
        h3.write("**% Change**")
        h4.write("**Market Cap**")
        h5.write("**Volume**")
        h6.write("**Action**") # names for each column in table 

        for item in sorted_market:
            color = "#00FF41" if item["% Change"] >= 0 else "#FF3131" # If the stock is growing, make it green, otherwise red
            
            # Format Market Cap 
            cap = item["Market Cap"]
            if cap >= 1e12: cap_str = f"${cap/1e12:.2f}T"
            elif cap >= 1e9: cap_str = f"${cap/1e9:.1f}B"
            else: cap_str = f"${cap/1e6:.1f}M" # Add T, B, or M for shorter names 
            
            # Add the data points to teh table 
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
 
 
#### Look at the alarmpage
def alarmpage():
    streamlit.set_page_config(page_title="Alarms | QuantView", layout="wide")

    # Home button 
    if streamlit.button("← Home"):
        streamlit.session_state.alarms = False
        streamlit.session_state.home = True
        streamlit.rerun()

    streamlit.markdown("<h1 style='text-align: center;'>Customize Alarms</h1>", unsafe_allow_html=True)
    
    # --- SECTION: ADD AN ALARM ---
    streamlit.markdown("<h3 style='text-align: center;'>Add an Alarm</h3>", unsafe_allow_html=True)
    
    # Formatting 
    col_size, col_stock, col_var, col_op, col_val, col_btn = streamlit.columns([1.5, 1.5, 2, 1, 1.5, 1.5])
    
    with col_size:
        size_choice = streamlit.selectbox("Size", ["Small", "Medium", "Loud"]) # Choose size of alarm 
    with col_stock:
        stock_input = streamlit.text_input("Stock", placeholder="AAPL") # Choose stock to monitor 
    with col_var:
        var_choice = streamlit.selectbox("Indicator", ["Price", "Volume", "% DELTA Price", "Alpha", "Beta", "EPS", "PE Ratio"]) # Which indicator to monitor
    with col_op:
        op_choice = streamlit.selectbox("Operator", [">", "<", ">=", "<=", "==", "!="]) # Which operator to assign?
    with col_val:
        val_input = streamlit.text_input("Target Value", placeholder="200.0") # Value of the indicator at which we trigger alarm 
    with col_btn:
        streamlit.markdown("<br>", unsafe_allow_html=True) # Align button
        if streamlit.button("Add Alarm", use_container_width=True): # This button adds an alarm 
            # Add an alarm here, using the correct subclass 
            if size_choice == "Small":
                temp_alarm = classes.SmallAlarm() 
            elif size_choice == "Medium":
                temp_alarm = classes.MediumAlarm()
            else:
                temp_alarm = classes.LoudAlarm()
            
            # Attempts to use setters to set in all the data inputted, 
            #if it works this entire array will be set to true, otherwise at least one will be false 
            success = [
                temp_alarm.set_stock(stock_input),
                temp_alarm.set_variable(var_choice),
                temp_alarm.set_operator(op_choice),
                temp_alarm.set_target(val_input)
            ]
            
            # 3. Only add if ALL setters passed
            if all(success):
                # Check if its a duplicate alarm 
                is_duplicate = False
                for existing in streamlit.session_state.alarm_list:
                    # Compare all attributes 
                    if (existing.get_stock() == temp_alarm.get_stock() and
                        existing.get_variable() == temp_alarm.get_variable() and
                        existing.get_operator() == temp_alarm.get_operator() and
                        existing.get_target() == temp_alarm.get_target()):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    streamlit.error(f"❌ You already have an alarm for {temp_alarm.get_stock()} with these exact settings!") # Do not add duplicate 
                else:
                    # Add to local and database if it is not a duplicate 
                    if streamlit.session_state.current_user:
                        database.save_alarm(streamlit.session_state.current_user, temp_alarm)
                    streamlit.session_state.alarm_list.append(temp_alarm)
                    streamlit.success(f"Added {size_choice} Alarm for {stock_input}!")
                    streamlit.rerun()

    streamlit.markdown("---")

    #  View alarms already added 
    streamlit.markdown("<h3 style='text-align: center;'>View Your Alarms</h3>", unsafe_allow_html=True)
    
    if not streamlit.session_state.alarm_list:
        streamlit.info("No alarms set. Create one above!")
    else:
        for index, alarm in enumerate(reversed(streamlit.session_state.alarm_list)): # NOTE TO IB ASSESSOR: enumerate is a for each loop that also gives the index numbers 
            with streamlit.container():
                real_index = len(streamlit.session_state.alarm_list) - 1 - index
                
                # Structured to 3 columns, Info, Reactivate, Remove
                c1, c2, c3 = streamlit.columns([6, 2, 2])
                
                with c1:
                    alarm_type = type(alarm).__name__ ## get the object type of the alarm 
                    color = "#2563EB" # set colour of the text depending on type of alarm 
                    if alarm_type == "MediumAlarm": color = "#F59E0B" 
                    elif alarm_type == "LoudAlarm": color = "#EF4444"

                    # Add a "(TRIGGERED)" tag if the alarm has been fired
                    status_text = ""
                    if alarm.is_fired():
                        status_text = f" <span style='color: {color}; font-weight: bold;'>[TRIGGERED]</span>"
                    
                    # Display 
                    streamlit.markdown(f"""
                    <div style='background: #161B22; padding: 15px; border-radius: 10px; border: 1px solid #30363D; border-left: 5px solid {color};'>
                        <strong style='color: {color};'>{alarm_type}</strong> | 
                        Stock: <b>{alarm.get_stock()}</b> | 
                        Condition: <b>{alarm.get_variable()} {alarm.get_operator()} {alarm.get_target()}</b>{status_text}
                    </div>
                    """, unsafe_allow_html=True)
                
                with c2:
                    streamlit.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    # ONLY show the Reactivate button if the alarm is already fired
                    if alarm.is_fired():
                        if streamlit.button("Reactivate", key=f"re_{real_index}", use_container_width=True): # If the user clicks the reactive button 
                            alarm.set_fired(False)
                            if streamlit.session_state.current_user:
                                database.update_alarm_fired_status( # Update database 
                                    streamlit.session_state.current_user,
                                    alarm.get_stock(),
                                    alarm.get_variable(),
                                    alarm.get_target(),
                                    False # Resetting to not fired
                                )
                            streamlit.success("Alarm Ready!")
                            streamlit.rerun()
                    else:
                        # Display a "Watching" label if not fired yet
                        streamlit.markdown("<p style='text-align:center; color:#8B949E; margin-top:15px;'>Monitoring...</p>", unsafe_allow_html=True)

                with c3: # Remove the alarm 
                    streamlit.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    if streamlit.button("Remove", key=f"del_{real_index}", use_container_width=True):
                        # Add to database 
                        if streamlit.session_state.current_user:
                            database.delete_alarm(streamlit.session_state.current_user, alarm.get_stock(), alarm.get_variable(), alarm.get_target())
                        streamlit.session_state.alarm_list.pop(real_index)
                        streamlit.rerun()
                
                streamlit.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
### Look at homescreen     
def homescreen():

    streamlit.set_page_config(page_title="Dashboard | QuantView", layout="wide")
    streamlit.markdown("<div class='dashboard-title'>QuantView Dashboard</div>", unsafe_allow_html=True)

    col_left, col_right = streamlit.columns([1.2, 1], gap="large")

    # Predefine some colours 
    COLOR_GREEN = "#00FF41" # Matrix Green
    COLOR_RED = "#FF3131"   # Neon Red

    # Market Watchlist
    with col_left:
        streamlit.markdown("### Market Watchlist")

        # Sorting UI 
        s1, s2 = streamlit.columns(2)
        sort_on = s1.selectbox("Sort By", ["Ticker", "Price", "Change", "Volume"], label_visibility="collapsed") 
        direction = s2.selectbox("Order", ["Ascending", "Descending"], label_visibility="collapsed")
        is_reverse = True if direction == "Descending" else False

        tickers = streamlit.session_state.watchlist 

        if not tickers:
            streamlit.info("Your watchlist is empty.")
        else:
            try:
                # Fetch data 
                data = yfinance.download(tickers, period="2d", interval="1d", progress=False)
                
                # Build a list of data objects
                watchlist_data = []
                for ticker in tickers:
                    if len(tickers) > 1:
                        close_series = data['Close'][ticker].dropna()
                        vol_series = data['Volume'][ticker].dropna()
                    else: # Yahoo finance doesn't return a 2d list if requesting only one stock 
                        close_series = data['Close'].dropna()
                        vol_series = data['Volume'].dropna()
                    
                    if not close_series.empty and len(close_series) >= 2: # If the stock has historic data (more than 2 days of past data)
                        # Find or calculate indicators 
                        curr = float(close_series.iloc[-1])
                        prev = float(close_series.iloc[-2])
                        change = ((curr - prev) / prev) * 100
                        vol = float(vol_series.iloc[-1]) 
                        
                        watchlist_data.append({ # append it to the list 
                            "Ticker": ticker,
                            "Price": curr,
                            "Change": change,
                            "Volume": vol
                        })
                    else:
                        watchlist_data.append({"Ticker": ticker, "Price": 0.0, "Change": 0.0, "Volume": 0}) # Otherwise just append empty

                # Sort it 
                sorted_watchlist = toolkit.merge_sort(watchlist_data, key=sort_on, reverse=is_reverse)

                # ender the table
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
                    
                    color = COLOR_GREEN if item["Change"] >= 0 else COLOR_RED # Colour it depending on the value 
                    sign = "+" if item["Change"] > 0 else ""

                    # Formatting Volume to be readable for ex 1M or 1B or 1T 
                    vol_display = f"{item['Volume']/1e6:.1f}M" if item['Volume'] >= 1e6 else f"{item['Volume']:,.0f}"

                    r1.markdown(f"**{ticker}**")
                    r2.write(f"${item['Price']:,.2f}")
                    r3.markdown(f"<span style='color:{color};'>{sign}{item['Change']:.2f}%</span>", unsafe_allow_html=True)
                    r4.write(vol_display)
                    
                    if r5.button("🗑️", key=f"del_watch_{ticker}"): # Delete it from watchlist 
                        streamlit.session_state.watchlist.remove(ticker)
                        if streamlit.session_state.current_user:
                            database.remove_watchlist(streamlit.session_state.current_user, ticker)
                        streamlit.rerun()

            except Exception as e:
                streamlit.error(f"Error loading watchlist: {e}")
    # S & P 500 performance panel 
    with col_right:
        streamlit.markdown("### S&P 500 Performance")
        sp_data = yfinance.download("^GSPC", period="1y", interval="1d", progress=False)
        
        if not sp_data.empty:
            chart_data = sp_data['Close']
            if hasattr(chart_data, 'columns'):# If chart_data is a DataFrame (multiple stocks), count the columns
                column_count = len(chart_data.columns)
            else: # If chart_data is just a single Series (one stock), default to 1
                column_count = 1
            chart_colors = ["#2563EB"] * column_count
            streamlit.line_chart(chart_data, height=280, color=chart_colors)
            
            # Calculate % Change of the S&P 500 for the Header
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
        # Buttons to look at other pages 
        if streamlit.button("View Stocks", key="home_view_btn", use_container_width=True):
            streamlit.session_state.home = False
            streamlit.session_state.lookup = True
            streamlit.rerun()

        if streamlit.button("Customize Alarms", key="home_alarm_btn", use_container_width=True):
            streamlit.session_state.home = False
            streamlit.session_state.alarms = True # Updated key
            streamlit.rerun()
            
            
    # Display all the notifications from the queue 
    streamlit.markdown("---")
    streamlit.markdown("<h3 style='text-align: center;'>Recent Notifications</h3>", unsafe_allow_html=True)
    
    q = streamlit.session_state.notif_queue
    
    # Use container to keep everything grouped
    with streamlit.container():
        if q.isEmpty(): # If the queue is empty display empty 
            streamlit.markdown("<p style='text-align: center; color: #8B949E;'>No recent notifications.</p>", unsafe_allow_html=True)
        else:
            items = q.get_all_items() # Function from my custom queue class that returns an arraylist containing every item from the queue in order
            
            for item in items: # Loop through every item 
                # Determine color based on alarm type 
                color = "#2563EB" # Default Blue
                if item['type'] == "MediumAlarm": color = "#F59E0B" # Orange
                if item['type'] == "LoudAlarm": color = "#EF4444"   # Red
                
                # Render each notification as a clean block
                streamlit.markdown(f"""
                <div style='background: #161B22; border: 1px solid #30363D; border-left: 5px solid {color}; border-radius: 8px; padding: 12px; margin-bottom: 10px;'>
                    <span style='color: #8B949E; font-size: 0.85rem;'>[{item['time']}]</span> 
                    <strong style='color: {color}; font-size: 1.1rem; margin-left: 10px;'>{item['stock']}</strong> 
                    <span style='color: #E6EDF3; margin-left: 5px;'>{item['variable']} triggered at <b>{item['value']:.2f}</b></span>
                </div>
                """, unsafe_allow_html=True)

            if streamlit.button("Clear Notification History", use_container_width=True):
                #Clear local Queue
                streamlit.session_state.notif_queue.clear()
                
                # Clear Database
                if streamlit.session_state.current_user:
                    database.clear_notifications(streamlit.session_state.current_user)
                    
                streamlit.rerun()
                
                
# Switch that routes the UI to whatever webpage the user is looking at right now
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

    
