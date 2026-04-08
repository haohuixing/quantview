### Imports from other libraries
import yfinance

# My custom SIMPLE ALPHA function - it calculates how well a stock performs against the S&P 500, but does not factor in Beta
def calcAlpha(ticker): # Math formula: Alpha = [(StockPrice_Now / StockPrice_Year_Ago - 1) - (IndexPrice_Now / IndexPrice_Year_Ago - 1)] * 100
    stock_h = ticker.history(period="1y")
    spy_h = yfinance.Ticker("^GSPC").history(period="1y")
    if len(stock_h) > 0 and len(spy_h) > 0:
        stock_perf = (stock_h['Close'].iloc[-1] / stock_h['Close'].iloc[0]) - 1
        spy_perf = (spy_h['Close'].iloc[-1] / spy_h['Close'].iloc[0]) - 1
        return (stock_perf - spy_perf) * 100
    return 0


# Merge sort 
# Key is what indicator to sort by, for example key = "volume' means mergesort sorts the stocks by volume
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