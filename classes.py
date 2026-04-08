# Imports from other libraries 
import streamlit
import yfinance
import base64

import toolkit #Modules by me


# Main abstract superclass for alarms 
class Alarm:
    def __init__(self, stock=None, variable=None, operator=None, target=None): # constructor
        # Initiate private variables 
        self.__stock = stock
        self.__variable = variable
        self.__operator = operator
        self.__target = target
        self.__fired = False  
        
        # Hashmap that converts name of the indicator in my app vs in yahoo finance for scraping purposes 
        self.__info_map = {
            "Price": "currentPrice",
            "Beta": "beta",
            "EPS": "trailingEps",
            "PE Ratio": "trailingPE",
            "Volume": "volume"  
        }

    # Setters (Encapsulation)
    # Every setter returns false if given invalid input, so that the main.py can know to reject the input, and true so main.py can accept it
    def set_stock(self, stock):
        if not stock or len(stock) < 1: # Check for empty ticker 
            streamlit.error("❌ Ticker cannot be empty")
            return False
        try: # Check if the ticker exists 
            check_ticker = yfinance.Ticker(stock)
            if check_ticker.fast_info.get('currency') is None:
                streamlit.error(f"❌ Ticker '{stock.upper()}' not found.")
                return False
                
            self.__stock = stock.upper()
            self.__fired = False 
            return True
        except Exception:
            streamlit.error(f"❌ Could not verify ticker '{stock}'.")
            return False
        
    def set_fired(self, status):
        if isinstance(status, bool): # Make sure is given bool
            self.__fired = status
            return True
        return False
        
    def set_variable(self, variable):
        valid_vars = ["Alpha", "Beta", "Price", "% DELTA Price", "EPS", "PE Ratio", "Volume"] # Possible valid indicators
        if variable in valid_vars:
            self.__variable = variable
            self.__fired = False # Reset to unfired when edited
            return True
        streamlit.error(f"❌ Variable '{variable}' is not supported.")
        return False

    def set_operator(self, operator):
        if operator in [">", "<", ">=", "<=", "==", "!="]: # Possible valid operators
            self.__operator = operator
            self.__fired = False # Reset to unfired when edited
            return True
        streamlit.error("❌ Invalid Operator")
        return False

    def set_target(self, target): 
        try:
            self.__target = float(target) # Make sure it is a number
            self.__fired = False # Reset to unfired when edited
            return True
        except:
            streamlit.error("❌ Invalid Target: Must be a number.")
            return False

    # Getters
    def get_stock(self): 
        return self.__stock
    def get_variable(self): 
        return self.__variable
    def get_operator(self): 
        return self.__operator
    def get_target(self): 
        return self.__target
    def is_fired(self): 
        return self.__fired

    ## Other functions
    
    def fetch_live_value(self): # Get live data, helper function 
        try:
            ticker = yfinance.Ticker(self.__stock)
            
            if self.__variable == "Price": # Find price 
                val = ticker.fast_info.get('last_price')
                if val is None or val == 0:
                    val = ticker.info.get('currentPrice')
                if val is None or val == 0:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        val = hist['Close'].iloc[-1]
                return val if val is not None else 0
            
            # Find alpha
            if self.__variable == "Alpha": # Simple Alpha does not include beta in its calculations 
                return toolkit.calcAlpha(ticker) # My custom alpha function 
            
            # Find % change in price 
            if self.__variable == "% DELTA Price":
                hist = ticker.history(period="5d")
                if len(hist) < 2: 
                    return 0
                
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2]
                
                # Formula: ((Current - Previous) / Previous) * 100
                percentage_change = ((current_price - previous_price) / previous_price) * 100
                return percentage_change
                
            # Find volume 
            if self.__variable == "Volume":
                # Try fast_info first for speed
                val = ticker.fast_info.get('last_volume')
                if val is None or val == 0:
                    val = ticker.info.get('volume')
                return val if val is not None else 0
            info = ticker.info
            yf_key = self.__info_map.get(self.__variable)
            return info.get(yf_key, 0)
            
        except Exception as e:
            print(f"Error fetching {self.__variable} for {self.__stock}: {e}")
            return None

    def check_alarm(self): # Check if the alarm should be fired or not. Returns a tuple (is fired or not, what value the indicator being monitored is at)
        # Uses private __fired
        if self.__fired: 
            return False, 0
        
        val = self.fetch_live_value()
        if val is None: 
            return False, 0
        
        op, target = self.__operator, self.__target
        ops = { # Combinations of operations between operator and target 
            ">": val > target, "<": val < target,
            ">=": val >= target, "<=": val <= target,
            "==": val == target, "!=": val != target
        }
        
        triggered = ops.get(op, False)
        if triggered: 
            self.__fired = True # Set the alarm to fired
        return triggered, val
        
    def play_local_sound(self, file_path): # Convert mp3 file to a format that streamlit can play 
        try:
            with open(file_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode()
                md = f"""
                    <audio autoplay style="display:none;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    </audio>
                    """
                streamlit.markdown(md, unsafe_allow_html=True)
        except FileNotFoundError:
            streamlit.error(f"🔊 Audio file not found: {file_path}")

    def raise_alarm(self, val): # Function that must use method overriding / polymorphism for sublcasses
        pass
        
# Subclasses for alarm 
class SmallAlarm(Alarm):
    def raise_alarm(self, val):
        streamlit.toast(f"🔔 {self.get_stock()} hit {val:.2f}", icon="ℹ️")
        self.play_local_sound("files/small.mp3")

class MediumAlarm(Alarm):
    def raise_alarm(self, val):
        streamlit.warning(f"⚠️ ALERT: {self.get_stock()} {self.get_variable()} is {val:.2f}")
        self.play_local_sound("files/medium.mp3")

class LoudAlarm(Alarm):
    def raise_alarm(self, val):
        streamlit.error(f"🚨 CRITICAL: {self.get_stock()} reached {val:.2f}!!")
        self.play_local_sound("files/big.mp3")
        
        # If the user does not block pop-ups, open the webpage to the stock for instant action
        url = f"https://finance.yahoo.com/quote/{self.get_stock()}"
        js = f"window.open('{url}', '_blank');"
        streamlit.components.v1.html(f"<script>{js}</script>", height=0, width=0)
        
        


############# QUEUE class 

class Queue:
    #Constructor: 
    #If max_size is an integer, the queue is static size 
    #If max_size is None, the queue is dynamic size
    def __init__(self, max_size=None):
        self.__items = []
        self.__max_size = max_size

    def enqueue(self, item): # Adds object to end of queue. 
        if self.isFull(): # If the queue is static and full, then we dequeue the oldest (first) item 
            self.dequeue()
            
        self.__items.append(item)
        return True

    def dequeue(self): # Removes the front (oldest) item from queue 
        if self.isEmpty():
            print("Error: Queue Empty")
            return None
        return self.__items.pop(0)

    def front(self): # Returns first item 
        if self.isEmpty(): return None
        return self.__items[0]

    def rear(self): # Returns last item 
        if self.isEmpty(): return None
        return self.__items[-1]

    def isEmpty(self): # checks if empty 
        return len(self.__items) == 0

    def isFull(self): # Checks if full, if it is a static queue. If dynamic, always false (can never be full)
        if self.__max_size is None:
            return False
        return len(self.__items) >= self.__max_size

    def size(self): # Return size 
        return len(self.__items)

    def get_all_items(self): # Returns an arraylist of all the items in the queue in order
        return self.__items[::-1]
        
    def clear(self): # Clears the enter queue 
        if not self.isEmpty():
            self.__items = []