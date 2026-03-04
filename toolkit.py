### Imports 
import yfinance


## WORK IN PROGRESS

def calcAlpha(ticker):
    stock_h = ticker.history(period="1y")
    spy_h = yfinance.Ticker("^GSPC").history(period="1y")
    if len(stock_h) > 0 and len(spy_h) > 0:
        stock_perf = (stock_h['Close'].iloc[-1] / stock_h['Close'].iloc[0]) - 1
        spy_perf = (spy_h['Close'].iloc[-1] / spy_h['Close'].iloc[0]) - 1
        return (stock_perf - spy_perf) * 100
    return 0

# toolkit.py

def merge_sort(arr, key, reverse=False):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key, reverse)
    right = merge_sort(arr[mid:], key, reverse)

    return merge(left, right, key, reverse)

def merge(left, right, key, reverse):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        # Comparison logic
        if not reverse:
            condition = left[i][key] <= right[j][key]
        else:
            condition = left[i][key] >= right[j][key]

        if condition:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result