import streamlit
from supabase import create_client
import hashlib
import classes

# --- 1. CONNECTION ---
# These will be pulled from Streamlit's secret vault
URL = streamlit.secrets["SUPABASE_URL"]
KEY = streamlit.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def hash_pw(password):
    """Secures passwords so even you can't read them in the DB."""
    return hashlib.sha256(password.encode()).hexdigest()

# --- 2. AUTHENTICATION ---
def signup(username, password):
    username = username.upper()
    hashed = hash_pw(password)
    try:
        supabase.table("users").insert({"username": username, "password_hash": hashed}).execute()
        return True
    except: return False

def login(username, password):
    username = username.upper()
    hashed = hash_pw(password)
    res = supabase.table("users").select("*").eq("username", username).eq("password_hash", hashed).execute()
    return len(res.data) > 0

# --- 3. WATCHLIST ---
def get_watchlist(username):
    res = supabase.table("watchlists").select("ticker").eq("username", username.upper()).execute()
    return [item['ticker'] for item in res.data]

def add_watchlist(username, ticker):
    supabase.table("watchlists").insert({"username": username.upper(), "ticker": ticker.upper()}).execute()

def remove_watchlist(username, ticker):
    supabase.table("watchlists").delete().eq("username", username.upper()).eq("ticker", ticker.upper()).execute()

# --- 4. ALARMS (Object Reconstruction) ---
def save_alarm(username, alarm_obj):
    data = {
        "username": username.upper(),
        "stock": alarm_obj.get_stock(),
        "variable": alarm_obj.get_variable(),
        "operator": alarm_obj.get_operator(),
        "target": alarm_obj.get_target(),
        "alarm_type": type(alarm_obj).__name__
    }
    supabase.table("alarms").insert(data).execute()

def load_alarms(username):
    res = supabase.table("alarms").select("*").eq("username", username.upper()).execute()
    obj_list = []
    for row in res.data:
        # Polymorphism: Create the right class type
        if row['alarm_type'] == "SmallAlarm": a = classes.SmallAlarm()
        elif row['alarm_type'] == "MediumAlarm": a = classes.MediumAlarm()
        else: a = classes.LoudAlarm()
        
        a.set_stock(row['stock'])
        a.set_variable(row['variable'])
        a.set_operator(row['operator'])
        a.set_target(row['target'])
        obj_list.append(a)
    return obj_list

def delete_alarm(username, stock, variable, target):
    supabase.table("alarms").delete().eq("username", username.upper()).eq("stock", stock).eq("variable", variable).eq("target", target).execute()

# --- 5. NOTIFICATIONS ---
def save_notification(username, notif_dict):
    data = {
        "username": username.upper(),
        "stock": notif_dict['stock'],
        "variable": notif_dict['variable'],
        "value": notif_dict['value'],
        "alarm_type": notif_dict['type']
    }
    supabase.table("notifications").insert(data).execute()

def load_notifications(username):
    res = supabase.table("notifications").select("*").eq("username", username.upper()).order('timestamp', desc=True).limit(10).execute()
    return res.data