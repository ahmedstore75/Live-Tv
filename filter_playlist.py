import requests
import re
from concurrent.futures import ThreadPoolExecutor

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# ১. মুভি, সিরিজ, ১৮+ এবং অপ্রয়োজনীয় ক্যাটাগরি সম্পূর্ণ ব্লক
BLOCK_KEYWORDS = [
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", "WEB SERIES", "MIX",
    "SONY LIV", "HOICHOI", "ZEE5", "NETFLIX", "AMAZON", "HOTSTAR", "ALT BALAJI",
    "SOUTH INDIA", "HOLLYWOOD", "BOLLYWOOD", "TAMIL |", "TELUGU |", 
    "KANNADA |", "MALAYALAM |", "BANGLA |", "HINDI |", "PUNJABI |",
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

# ২. জনপ্রিয় চ্যানেল ও খেলার কিওয়ার্ড
POPULAR_BD = ["SOMOY", "INDEPENDENT", "JAMUNA", "24", "EKBATTOR", "NTV", "ATN", "CHANNEL I", "DEEPTO", "GTV", "T SPORTS", "RTV", "MASRANGA", "BTV", "BENGAL"]
POPULAR_IN = ["STAR PLUS", "SONY SAB", "ZEE TV", "COLORS", "STAR BHARAT", "SONY MAX", "STAR MOVIES", "ZEE CINEMA", "ANANDABAZAR", "ABP", "AAJ TAK"]
POPULAR_PAK = ["GEO", "ARY", "HUM", "DUNYA", "EXPRESS", "PTV"]
SPORTS_KEYWORDS = ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS", "WILLOW", "BEIN", "EUROSPORT", "ASTRO", "SUPERSPORT", "CANAL+", "SKY SPORTS", "ARENA"]

YEAR_PATTERN = re.compile(r'\(?20[0-2][0-9]\)?')
SEASON_EPISODE_PATTERN = re.compile(r'\b(S\d{1,2}|E\d{1,3}|EP\d{1,3}|EPISODE)\b', re.IGNORECASE)

# চ্যানেল সক্রিয় (Active) কি না চেক করার ফাংশন
def is_channel_active(channel_tuple):
    line, stream_url = channel_tuple
    try:
        res = requests.head(stream_url, headers=headers, timeout=2.5, allow_redirects=True)
        if res.status_code == 200:
            return channel_tuple
        res_get = requests.get(stream_url, headers=headers, timeout=2.5, stream=True)
        if res_get.status_code == 200:
            return channel_tuple
    except:
        pass
    return None

try:
    print("Downloading and processing playlist...")
    response = requests.get(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        lines = response.text.splitlines()
        
        bd_raw = []
        sports_raw = []
        in_pak_raw = []
        
        seen_urls = set()
        seen_names = set()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXTINF:"):
                stream_url = lines[i + 1].strip() if (i + 1 < len(lines) and not lines[i + 1].startswith("#")) else ""
                
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                group_title = group_match.group(1).upper() if group_match else ""
                channel_name = line.split(",")[-1].strip().upper() if "," in line else line.upper()

                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)
                has_year = bool(YEAR_PATTERN.search(group_title)) or bool(YEAR_PATTERN.search(channel_name))
                has_season_ep = bool(SEASON_EPISODE_PATTERN.search(channel_name)) or bool(SEASON_EPISODE_PATTERN.search(group_title))

                if not is_blocked and not has_year and not has_season_ep and stream_url:
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        channel_block = (line, stream_url)

                        # ক. বাংলাদেশ জনপ্রিয় চ্যানেল (১ম পজিশন)
                        if any(bd in group_title or bd in channel_name for bd in ["BANGLA", "BANGLADESH", "BD"]):
                            if any(pop in channel_name for pop in POPULAR_BD) or "BD" in group_title:
                                bd_raw.append(channel_block)
                                seen_urls.add(stream_url)
                                seen_names.add(channel_name)

                        # খ. সব দেশের অল স্পোর্টস চ্যানেল (২য় পজিশন)
                        elif any(sp in group_title or sp in channel_name for sp in SPORTS_KEYWORDS):
                            sports_raw.append(channel_block)
                            seen_urls.add(stream_url)
                            seen_names.add(channel_name)

                        # গ. ইন্ডিয়া ও পাকিস্তানের জনপ্রিয় চ্যানেল (৩য় পজিশন)
                        elif any(other in group_title or other in channel_name for other in ["INDIA", "INDIAN", "HINDI", "PAKISTAN", "PAK"]):
                            if any(pop in channel_name for pop in POPULAR_IN + POPULAR_PAK):
                                in_pak_raw.append(channel_block)
                                seen_urls.add(stream_url)
                                seen_names.add(channel_name)

                if stream_url:
                    i += 1
            i += 1

        print("Testing active status for filtered popular channels...")
        all_raw = bd_raw + sports_raw + in_pak_raw
        active_channels = []
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(is_channel_active, all_raw)
            for res in results:
                if res:
                    active_channels.append(res)

        # M3U ফাইল তৈরি
        final_playlist = ["#EXTM3U"]
        for item in active_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print(f"✅ Finished! Total Active Selected Channels: {len(active_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
