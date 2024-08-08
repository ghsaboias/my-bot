import asyncio
import json
import websockets
import aiohttp
from collections import deque
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configuration
coins_to_monitor = ["btcusdt"]
one_second_threshold = 0.1
one_min_threshold = 1.0
five_min_threshold = 2.0
pushover_user_key = os.getenv("PUSHOVER_USER_KEY")
pushover_api_token = os.getenv("PUSHOVER_API_TOKEN")

# Store historical prices
historical_prices = {coin: deque(maxlen=600) for coin in coins_to_monitor}

# Notification counters
notifications_sent = {'minute': 0, 'day': 0}
last_min_check = datetime.now(timezone.utc)
last_day_check = datetime.now(timezone.utc)

# Interval trackers
last_one_min_check = {coin: datetime.now(timezone.utc) for coin in coins_to_monitor}
last_five_min_check = {coin: datetime.now(timezone.utc) for coin in coins_to_monitor}

# Track bot initialization time
bot_start_time = datetime.now(timezone.utc)

# New: Notification queue
notification_queue = asyncio.Queue()

async def add_to_queue(symbol, message):
    await notification_queue.put((symbol, message))

async def send_notification(symbol, message):
    global notifications_sent, last_min_check, last_day_check

    now = datetime.now(timezone.utc)
    if now - last_min_check > timedelta(minutes=1):
        notifications_sent['minute'] = 0
        last_min_check = now
    if now - last_day_check > timedelta(days=1):
        notifications_sent['day'] = 0
        last_day_check = now

    # New: Check against new limits and queue if necessary
    if notifications_sent['minute'] >= 3 or notifications_sent['day'] >= 200:
        print("Notification limit reached. Queueing notification.")
        await add_to_queue(symbol, message)
        return

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": pushover_api_token,
                    "user": pushover_user_key,
                    "message": message,
                }
            ) as response:
                if response.status != 200:
                    print(f"Error sending notification: {response.status} {response.reason}")
    except Exception as e:
        print(f"Exception sending notification: {e}")
    print(f"Notification sent:\n{message}")

    notifications_sent['minute'] += 1
    notifications_sent['day'] += 1

# New: Process queued notifications
async def process_notification_queue():
    while True:
        try:
            symbol, message = await notification_queue.get()
            await send_notification(symbol, message)
            
            # If we've hit the per-minute limit, wait until the next minute
            if notifications_sent['minute'] >= 3:
                seconds_to_next_min = 60 - datetime.now(timezone.utc).second
                await asyncio.sleep(seconds_to_next_min)
        except Exception as e:
            print(f"Error processing notification queue: {e}")
        finally:
            notification_queue.task_done()

def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

async def handle_message(message, initial_prices_sent):
    try:
        data = json.loads(message)
        symbol = data.get('s', '').lower()
        if not symbol or symbol not in coins_to_monitor:
            return

        current_price = float(data['c'])
        timestamp = datetime.now(timezone.utc)

        if not initial_prices_sent[symbol]:
            await send_notification(symbol, f"{symbol.upper()} Initial Price: ${current_price:.4f}")
            initial_prices_sent[symbol] = True

        prices = historical_prices[symbol]
        if len(prices) >= 2:
            await check_price_changes(symbol, current_price, prices, timestamp)

        prices.append((timestamp, current_price))

    except Exception as e:
        print(f"{get_timestamp()} - Exception handling message: {e}")

async def check_price_changes(symbol, current_price, prices, timestamp):
    try:
        # Check sudden price change (1 second)
        past_price = prices[-1][1]
        change = (current_price - past_price) / past_price * 100
        if abs(change) >= one_second_threshold:
            await send_notification(symbol, f"{symbol.upper()} 1s 🚨:\nPrice now: ${current_price:.4f}\nPrice 1s ago: ${past_price:.4f}\nChange: {change:.4f}%")
            print(f"{get_timestamp()} - {symbol.upper()} 1s price change detected: {change:.4f}%")
        else:
            print(f"{get_timestamp()} - {len(prices)} {symbol.upper()} 1s change: {change:.4f}%; Price: ${current_price:.4f}; Prev. price: ${past_price:.4f}")

        # Check 1 minute interval
        if len(prices) >= 60:
            if timestamp - last_one_min_check[symbol] >= timedelta(minutes=1):
                past_price_1_min = prices[-60][1]
                change_1_min = (current_price - past_price_1_min) / past_price_1_min * 100
                if abs(change_1_min) >= one_min_threshold:
                    await send_notification(symbol, f"{symbol.upper()} 1min 🚨:\nPrice now: ${current_price:.4f}\nPrice 1min ago: ${past_price_1_min:.4f}\nChange: {change_1_min:.4f}%")
                    print(f"{get_timestamp()} - {symbol.upper()} 1min price change detected: {change_1_min:.4f}%")
                else:
                    print(f"{get_timestamp()} - {symbol.upper()} 1min price change: {change_1_min:.4f}%")
                last_one_min_check[symbol] = timestamp

        # Check 5 minute interval (updated)
        if len(prices) >= 300 and timestamp - last_five_min_check[symbol] >= timedelta(minutes=5):
            last_5_min_price = prices[0][1]
            change_5_min = (current_price - last_5_min_price) / last_5_min_price * 100
            message = f"{symbol.upper()} 5min update:\nPrice now: ${current_price:.4f}\nPrice 5min ago: ${last_5_min_price:.4f}\nChange: {change_5_min:.4f}%"
            if abs(change_5_min) >= five_min_threshold:
                message = f"{symbol.upper()} 5min 🚨:\n" + message
            await send_notification(symbol, message)
            last_five_min_check[symbol] = timestamp

    except Exception as e:
        print(f"{get_timestamp()} - Exception in check_price_changes for {symbol}: {e}")

async def connect_and_listen():
    uri = "wss://stream.binance.com:9443/ws"
    streams = "/".join([f"{coin}@ticker" for coin in coins_to_monitor])
    initial_prices_sent = {coin: False for coin in coins_to_monitor}

    while True:
        try:
            async with websockets.connect(f"{uri}/{streams}") as websocket:
                print(f"{get_timestamp()} - Connected to WebSocket for streams: {streams}")
                async for message in websocket:
                    await handle_message(message, initial_prices_sent)
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"{get_timestamp()} - WebSocket connection closed: {e}. Reconnecting...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"{get_timestamp()} - Exception in WebSocket connection: {e}. Reconnecting...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(process_notification_queue())  # New: Start the queue processor
    loop.run_until_complete(connect_and_listen())