# Imports from other libraries 
import streamlit
from supabase import create_client

# My own module
import classes

# Get database key and URL from secrets file (link to supabase and api key)
URL = streamlit.secrets["SUPABASE_URL"]
KEY = streamlit.secrets["SUPABASE_KEY"]
supabase = create_client(URL, KEY)

def make_hidden_email(username): # Converts username into an email (supabase creates accounts using email)
    clean = "".join(char for char in username if char.isalnum()).lower()
    return f"{clean}@quantview.com"

def signup(username, password): # Attempt to sign up a user 
    email = make_hidden_email(username) # Convert a username into an email 
    try:
        #Create the Auth account
        auth_res = supabase.auth.sign_up({"email": email, "password": password})
        
        #Attempt to add them to the public.users table
        try:
            supabase.table("users").insert({"username": username.upper()}).execute()
        except:
            return False  

        # Now log them in 
        return login(username, password)
        
    except Exception as e:
        print(f"Signup Error: {e}")
        return False

def login(username, password): # attempt to log in
    email = make_hidden_email(username)
    try:
        supabase.auth.sign_in_with_password({"email": email, "password": password})
        return True
    except Exception as e:
        print(f"Login Error: {e}")
        return False

def get_watchlist(username):  # Retrieve watchlist from database 
    res = supabase.table("watchlists").select("ticker").eq("username", username.upper()).execute()
    return list(set([item['ticker'] for item in res.data]))

def add_watchlist(username, ticker): # update database with watchlist items
    supabase.table("watchlists").insert({"username": username.upper(), "ticker": ticker.upper()}).execute()

def remove_watchlist(username, ticker): # update database with watchlist items
    supabase.table("watchlists").delete().eq("username", username.upper()).eq("ticker", ticker.upper()).execute()

def save_notification(username, notif_dict): # update database with notification items
    data = {
        "username": username.upper(),
        "stock": notif_dict['stock'],
        "variable": notif_dict['variable'],
        "value": notif_dict['value'],
        "alarm_type": notif_dict['type']
    }
    supabase.table("notifications").insert(data).execute()

def load_notifications(username): #Retrieve notifications from database
    res = supabase.table("notifications").select("*").eq("username", username.upper()).order('id', desc=True).limit(10).execute()
    return res.data

def clear_notifications(username): # clear database from notification items
    supabase.table("notifications").delete().eq("username", username.upper()).execute()

def update_alarm_fired_status(username, stock, variable, target, fired): # Update if an alarm is fired or not 
    supabase.table("alarms").update({"fired": fired}).eq("username", username.upper()).eq("stock", stock).eq("variable", variable).eq("target", target).execute()

def save_alarm(username, alarm_obj): # save an alarm to database
    data = {
        "username": username.upper(),
        "stock": alarm_obj.get_stock(),
        "variable": alarm_obj.get_variable(),
        "operator": alarm_obj.get_operator(),
        "target": alarm_obj.get_target(),
        "alarm_type": type(alarm_obj).__name__,
        "fired": alarm_obj.is_fired()
    }
    supabase.table("alarms").insert(data).execute()

def load_alarms(username): # Load all the alarms to local session state from database
    res = supabase.table("alarms").select("*").eq("username", username.upper()).execute()
    obj_list = []
    for row in res.data:
        if row['alarm_type'] == "SmallAlarm": a = classes.SmallAlarm()
        elif row['alarm_type'] == "MediumAlarm": a = classes.MediumAlarm()
        else: a = classes.LoudAlarm()
        a.set_stock(row['stock']); a.set_variable(row['variable']); a.set_operator(row['operator']); a.set_target(row['target'])
        a.set_fired(row.get('fired', False))
        obj_list.append(a)
    return obj_list

def delete_alarm(username, stock, variable, target): # delete the alarm from the database
    supabase.table("alarms").delete().eq("username", username.upper()).eq("stock", stock).eq("variable", variable).eq("target", target).execute()