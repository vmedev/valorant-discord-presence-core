import os
import requests
from collections import Counter
from config import PUUID, NICKNAME, TAG, REGION

API_KEY = os.getenv("HENRIK_KEY") # Your can paste here yor api key instead of os.getenv("HENRIK_KEY"), but it not safe
if not API_KEY:
    raise RuntimeError("HENRIK_KEY is not set")

MATCH_SIZE = 10

session = requests.Session()
session.headers.update({"Authorization": API_KEY})


def get_puuid(nickname: str, tag: str) -> str:
    puuid_url = f"https://api.henrikdev.xyz/valorant/v1/account/{nickname}/{tag}"
    response = session.get(puuid_url, timeout=30)
    response.raise_for_status()

    response_json = response.json()
    puuid = response_json.get("data", {}).get("puuid")

    if not puuid:
        raise RuntimeError("Failed to get puuid from API response")

    return puuid


def find_me(match: dict, puuid: str):
    if not isinstance(match, dict):
        return None

    players = match.get("players") or {}
    all_players = players.get("all_players") or []

    for player in all_players:
        if player.get("puuid") == puuid:
            return player

    return None


def kd_from_matches(matches: list, puuid: str):
    kills = deaths = used = 0

    for match in matches:
        me = find_me(match, puuid)
        if not me:
            continue

        stats = me.get("stats") or {}
        kills += int(stats.get("kills", 0) or 0)
        deaths += int(stats.get("deaths", 0) or 0)
        used += 1

    kd = kills / max(1, deaths)
    return {"matches": used, "kills": kills, "deaths": deaths, "kd": kd}


def favorite_agent_from_matches(matches: list, puuid: str):
    counter = Counter()
    used = 0

    for match in matches:
        me = find_me(match, puuid)
        if not me:
            continue

        agent = me.get("character") or me.get("agent") or "Unknown"
        counter[agent] += 1
        used += 1

    agent, count = counter.most_common(1)[0] if counter else ("Unknown", 0)
    return {"matches": used, "agent": agent, "count": count}


def get_stats() -> dict:
    puuid = PUUID if PUUID else get_puuid(NICKNAME, TAG)

    matches_url = (
        f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{REGION}/{puuid}"
        f"?size={MATCH_SIZE}&mode=competitive"
    )

    matches_resp = session.get(matches_url, timeout=30)
    matches_resp.raise_for_status()
    matches_json = matches_resp.json()

    matches = matches_json.get("data", [])
    kd_info = kd_from_matches(matches, puuid)
    fav_agent_info = favorite_agent_from_matches(matches, puuid)

    mmr_url = f"https://api.henrikdev.xyz/valorant/v2/by-puuid/mmr/{REGION}/{puuid}"
    mmr_resp = session.get(mmr_url, timeout=30)
    mmr_resp.raise_for_status()
    mmr_json_data = mmr_resp.json()

    current = mmr_json_data["data"]["current_data"]
    rank_name = current["currenttierpatched"]
    rr = current["ranking_in_tier"]
    rr_delta = current.get("mmr_change_to_last_game")

    return {
        "matches": kd_info["matches"],
        "kills": kd_info["kills"],
        "deaths": kd_info["deaths"],
        "kd": round(kd_info["kd"], 2),
        "rank": f"{rank_name}, {rr} RR",
        "rr_delta": rr_delta,
        "mode": "Competitive",
        "favorite_agent": fav_agent_info["agent"],
        "favorite_agent_games": fav_agent_info["count"],
    }