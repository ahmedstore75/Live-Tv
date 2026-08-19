import requests
import re
from concurrent.futures import ThreadPoolExecutor

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# অপ্রয়োজনীয় VOD, এপিসোড কার্টুন, ইউএস অডিও মিউজিক, মুভি এবং ১৮+ সম্পূর্ণ ব্লক
BLOCK_KEYWORDS = [
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", "WEB SERIES", "MIX",
    "SCOOBY", "TOM & JERRY", "TOM AND JERRY", "MOTU_PATLU", "MOTU PATLU", "CHOTA BHEEM", "CHOTA_BHEEM",
    "US-MUSIC", "MUSIC CHOICE", "CHOICE |", "RADIO", "AUDIO",
    "SONY LIV", "HOICHOI", "ZEE5", "NETFLIX", "AMAZON", "HOTSTAR",
    "SOUTH INDIA", "HOLLYWOOD", "BOLLYWOOD",
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

# ইন্ডিয়ান বাংলা চ্যানেলের নামসমূহ
INDIAN_BANGLA_CHANNELS = [
    "ZEE BANGLA", "STAR JALSHA", "COLORS BANGLA", "JALSHA MOVIES", 
    "ZEE BANGLA CINEMA", "SONY AATH", "AKASH AATH", "NEWS18 BANGLA", 
    "ABP ANANDA", "CALCUTTA NEWS", "TV9 BANGLA", "ENTER10 RANGEELA"
]

YEAR_PATTERN = re.compile(r'\(?20[0-2][0-9]\)?')
SEASON_EPISODE_PATTERN = re.compile(r'\b(S\d{1,2}|E\d{1,3}|EP\d{1,3}|EPISODE|\*\d+)\b', re.IGNORECASE)

def rewrite_category(line, new_category):
    return re.sub(r'group-title="[^"]*"', f'group-title="{new_category}"', line, flags=re.IGNORECASE)

# সক্রিয় (Active) চ্যানেল চেক করার ফাংশন
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
    print("Downloading playlist...")
    response = requests.get(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        lines = response.text.splitlines()
        
        categories = {
            "BANGLADESH": [],
            "INDIAN BANGLA": [],
            "SPORTS": [],
            "INDIAN": [],
            "ISLAMIC": [],
            "DOCUMENTARY": [],
            "MUSIC": [],
            "KIDS": [],
            "NEWS": []
        }
        
        seen_urls = set()
        seen_names = set()
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXTINF:"):
                stream_url = lines[i + 1].strip() if (i + 1 < len(lines) and not lines[i + 1].startswith("#")) else ""
                
                group_match = re.search(r'group-title="[^"]*"', line, re.IGNORECASE)
                group_title = group_match.group(1).upper() if group_match else ""
                channel_name = line.split(",")[-1].strip().upper() if "," in line else line.upper()

                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)
                has_year = bool(YEAR_PATTERN.search(group_title)) or bool(YEAR_PATTERN.search(channel_name))
                has_season_ep = bool(SEASON_EPISODE_PATTERN.search(channel_name)) or bool(SEASON_EPISODE_PATTERN.search(group_title))

                # এপিসোড/ভিডিও ফাইল বাদ দেওয়া (যেমন: Star 1, Star 2 ইত্যাদি সংখ্যা যুক্ত অহেতুক ফাইল)
                is_file_number = bool(re.search(r'\b\d{1,3}\b$', channel_name)) and not any(tv in channel_name for tv in ["24", "24/7", "9X", "TV9"])

                if not is_blocked and not has_year and not has_season_ep and not is_file_number and stream_url:
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        
                        # ১. ইন্ডিয়ান বাংলা চ্যানেল
                        if any(ib in channel_name for ib in INDIAN_BANGLA_CHANNELS) or "WEST BENGAL" in group_title or "INDIAN BANGLA" in group_title:
                            updated_line = rewrite_category(line, "INDIAN BANGLA")
                            categories["INDIAN BANGLA"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ২. ইসলামিক চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["ISLAM", "ISLAMIC", "MADANI", "PEACE TV", "MAKKAH", "MADINAH", "SUNNAH"]):
                            updated_line = rewrite_category(line, "ISLAMIC")
                            categories["ISLAMIC"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৩. ডকুমেন্টারি চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["DISCOVERY", "NAT GEO", "NATIONAL GEOGRAPHIC", "ANIMAL PLANET", "HISTORY", "DOCUMENTARY"]):
                            updated_line = rewrite_category(line, "DOCUMENTARY")
                            categories["DOCUMENTARY"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৪. মিউজিক চ্যানেল (শুধু টিভি চ্যানেল)
                        elif any(k in group_title or k in channel_name for k in ["MTV", "9XM", "ZOOM", "SANGEET", "GANA", "9X MUSIC", "MUSIC INDIA", "MASTIII"]):
                            updated_line = rewrite_category(line, "MUSIC")
                            categories["MUSIC"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৫. কিডস লাইভ চ্যানেল (Nick, Disney, Cartoon Network)
                        elif any(k in group_title or k in channel_name for k in ["CARTOON NETWORK", "NICK", "POGO", "DISNEY", "SONY YAY", "HUNGAMA"]):
                            updated_line = rewrite_category(line, "KIDS")
                            categories["KIDS"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৬. স্পোর্টস চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS", "WILLOW", "BEIN", "EUROSPORT", "T SPORTS", "GTV"]):
                            updated_line = rewrite_category(line, "SPORTS")
                            categories["SPORTS"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৭. বাংলাদেশ টিভি চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["BANGLA", "BANGLADESH", "BD"]):
                            updated_line = rewrite_category(line, "BANGLADESH")
                            categories["BANGLADESH"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৮. ইন্ডিয়ান চ্যানেল (হিন্দি/অন্যান্য)
                        elif any(k in group_title or k in channel_name for k in ["INDIA", "INDIAN", "HINDI", "STAR PLUS", "ZEE TV", "COLORS", "SONY SAB", "STAR MOVIES", "ZEE CINEMA"]):
                            updated_line = rewrite_category(line, "INDIAN")
                            categories["INDIAN"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                if stream_url:
                    i += 1
            i += 1

        all_selected = []
        for cat_list in categories.values():
            all_selected.extend(cat_list)

        print("Testing active status for channels...")
        active_channels = []
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = executor.map(is_channel_active, all_selected)
            for res in results:
                if res:
                    active_channels.append(res)

        final_playlist = ["#EXTM3U"]
        for item in active_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print(f"✅ Filtered Successfully! Total Active Channels: {len(active_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
