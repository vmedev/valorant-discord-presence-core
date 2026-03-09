# This version is console only console programm
import time
import threading
from datetime import datetime

from config import DISCORD_CLIENT_ID, UPDATE_INTERVAL, Refresh_Api
from valorant_api import get_stats
from presence import DiscordPresence

stop_event = threading.Event()
lock = threading.Lock()

latest_stats = None
latest_error = None
last_api_time = None


def api_loop():
    global latest_stats, latest_error, last_api_time

    while not stop_event.is_set():
        try:
            stats = get_stats()
            with lock:
                latest_stats = stats
                latest_error = None
                last_api_time = datetime.now()
            print(f"[API] Stats updated at {last_api_time.strftime('%H:%M:%S')}")
        except BaseException as e:
            with lock:
                latest_error = str(e)
            print(f"[API ERROR] {e}")

        stop_event.wait(Refresh_Api)


def rpc_loop():
    global latest_error

    try:
        presence = DiscordPresence(DISCORD_CLIENT_ID)
        print("[RPC] Discord RPC connected")
    except Exception as e:
        with lock:
            latest_error = f"Discord RPC init error: {e}"
        print(f"[RPC ERROR] Discord RPC init error: {e}")
        return

    while not stop_event.is_set():
        with lock:
            stats = latest_stats
            err = latest_error

        if stats and not err:
            try:
                presence.update(stats)
                print("[RPC] Presence updated")
            except Exception as e:
                with lock:
                    latest_error = f"Discord RPC update error: {e}"
                print(f"[RPC ERROR] Discord RPC update error: {e}")

        stop_event.wait(UPDATE_INTERVAL)


def force_refresh():
    global latest_stats, latest_error, last_api_time

    try:
        stats = get_stats()
        with lock:
            latest_stats = stats
            latest_error = None
            last_api_time = datetime.now()
        print(f"[API] Initial stats loaded at {last_api_time.strftime('%H:%M:%S')}")
    except BaseException as e:
        with lock:
            latest_error = str(e)
        print(f"[API ERROR] {e}")


def print_status_loop():
    while not stop_event.is_set():
        with lock:
            stats = latest_stats
            err = latest_error
            t = last_api_time

        if err:
            print(f"[STATUS] ERROR: {err}")
        elif not stats:
            print("[STATUS] Loading stats...")
        else:
            rank = stats.get("rank", "Unknown")
            kd = stats.get("kd", "?")
            fav = stats.get("fav_agent") or stats.get("favorite_agent") or "Unknown"
            api_time = t.strftime("%H:%M:%S") if t else "?"
            print(f"[STATUS] Rank: {rank} | KD: {kd} | Fav agent: {fav} | API: {api_time}")

        stop_event.wait(10)


def main():
    print("Starting Valorant Presence (console mode)...")
    print("CLIENT_ID:", DISCORD_CLIENT_ID)

    force_refresh()

    threading.Thread(target=api_loop, daemon=True).start()
    threading.Thread(target=rpc_loop, daemon=True).start()
    threading.Thread(target=print_status_loop, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_event.set()


if __name__ == "__main__":
    main()