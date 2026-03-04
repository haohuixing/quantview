####
# THIS IS MY TO DO LIST, NOT FOR YOU GEMINI DONT READ THIS YET 

# IMPLEMENT MERGE SORT: (recursion + use of merging sorted lists)
# - merge sort stocks into "sort by best" for original algorithm, thus must use my own 
# Add two-d array 
#
#
#
# TO DO LIST TMMRW: 
# - Then work on the "look up stocks page"
#
#
#

import streamlit
import yfinance
import base64

import toolkit #by me

class Alarm:
    def __init__(self, stock=None, variable=None, operator=None, target=None):
        # All variables are now private
        self.__stock = stock
        self.__variable = variable
        self.__operator = operator
        self.__target = target
        self.__fired = False  # Changed to private

        self.__info_map = {
            "Price": "currentPrice",
            "Beta": "beta",
            "EPS": "trailingEps",
            "PE Ratio": "trailingPE",
            "Volume": "volume"  
        }

    # --- SETTERS (Encapsulation) ---
    def set_stock(self, stock):
        if stock and len(stock) >= 1:
            self.__stock = stock.upper()
            self.__fired = False  # Reset status when edited
            return True
        streamlit.error("❌ Invalid Ticker")
        return False

    def set_variable(self, variable):
        valid_vars = ["Alpha", "Beta", "Price", "% DELTA Price", "EPS", "PE Ratio", "Volume"]
        if variable in valid_vars:
            self.__variable = variable
            self.__fired = False # Reset status when edited
            return True
        streamlit.error(f"❌ Variable '{variable}' is not supported.")
        return False

    def set_operator(self, operator):
        if operator in [">", "<", ">=", "<=", "==", "!="]:
            self.__operator = operator
            self.__fired = False # Reset status when edited
            return True
        streamlit.error("❌ Invalid Operator")
        return False

    def set_target(self, target):
        try:
            self.__target = float(target)
            self.__fired = False # Reset status when edited
            return True
        except:
            streamlit.error("❌ Invalid Target: Must be a number.")
            return False

    # --- GETTERS ---
    def get_stock(self): return self.__stock
    def get_variable(self): return self.__variable
    def get_operator(self): return self.__operator
    def get_target(self): return self.__target
    
    def is_fired(self): 
        """Getter for the fired status."""
        return self.__fired

    def reactivate(self):
        """Setter to reset the fired status to False."""
        self.__fired = False

    # --- THE DATA LOGIC ---
    def fetch_live_value(self):
        try:
            # Always use the getter or the private attribute internally
            ticker = yfinance.Ticker(self.__stock)
            
            if self.__variable == "Price":
                val = ticker.fast_info.get('last_price')
                if val is None or val == 0:
                    val = ticker.info.get('currentPrice')
                if val is None or val == 0:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        val = hist['Close'].iloc[-1]
                return val if val is not None else 0

            if self.__variable == "Alpha": # Simple Alpha does not include beta in its calculations 
                return toolkit.calcAlpha(ticker)
        
            if self.__variable == "% DELTA Price":
                hist = ticker.history(period="5d")
                if len(hist) < 2: 
                    return 0
                
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2]
                
                # Formula: ((Current - Previous) / Previous) * 100
                percentage_change = ((current_price - previous_price) / previous_price) * 100
                return percentage_change
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

    def check_alarm(self):
        # Uses private __fired
        if self.__fired: return False, 0
        
        val = self.fetch_live_value()
        if val is None: return False, 0
        
        op, target = self.__operator, self.__target
        ops = {
            ">": val > target, "<": val < target,
            ">=": val >= target, "<=": val <= target,
            "==": val == target, "!=": val != target
        }
        
        triggered = ops.get(op, False)
        if triggered: 
            self.__fired = True # Internal update to private variable
        return triggered, val
        
    def play_local_sound(self, file_path):
        """Standard method to handle audio injection."""
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

    def raise_alarm(self, val):
        """To be overridden by subclasses (Polymorphism)."""
        pass
# --- SUBCLASSES (Polymorphism) ---

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
    def __init__(self, max_size=None):
        """
        Constructor: 
        If max_size is an integer, the queue is Static.
        If max_size is None, the queue is Dynamic.
        """
        self.__items = []
        self.__max_size = max_size

    def enqueue(self, item):
        """Adds an item. If static and full, removes oldest to maintain size."""
        if self.isFull():
            # For a notification system, we dequeue the oldest to make room
            self.dequeue()
            
        self.__items.append(item)
        return True

    def dequeue(self):
        """Removes front item. Includes empty check for rubric compliance."""
        if self.isEmpty():
            print("Error: Queue Empty")
            return None
        return self.__items.pop(0)

    def front(self):
        if self.isEmpty(): return None
        return self.__items[0]

    def rear(self):
        if self.isEmpty(): return None
        return self.__items[-1]

    def isEmpty(self):
        return len(self.__items) == 0

    def isFull(self):
        """Proper check for full queue."""
        if self.__max_size is None:
            return False
        return len(self.__items) >= self.__max_size

    def size(self):
        return len(self.__items)

    def get_all_items(self):
        """Returns items newest-to-oldest for the UI."""
        return self.__items[::-1]
        
    def clear(self):
        """Resets the queue to an empty state."""
        if not self.isEmpty():
            self.__items = []