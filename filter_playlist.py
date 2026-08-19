import requests
import re
from concurrent.futures import ThreadPoolExecutor

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# বাদ দেওয়ার কীওয়ার্ডসমূহ (VOD, কার্টুন ভিডিও, মুভি, ১৮+)
BLOCK_KEYWORDS = [
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", "WEB SERIES", "MIX",
    "MOTU_PATLU", "MOTU PATLU", "CHOTA BHEEM", "CHOTA_BHEEM", "PUNJABI",
    "SONY LIV", "HOICHOI", "ZEE5", "NETFLIX", "AMAZON", "HOTSTAR",
    "SOUTH INDIA", "HOLLYWOOD", "BOLLYWOOD",
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

YEAR_PATTERN = re.compile(r'\(?20[0-2][0-9]\)?')
SEASON_EPISODE_PATTERN = re.compile(r'\b(S\d{1,2}|E\d{1,3}|EP\d{1,3}|EPISODE)\b', re.IGNORECASE)

# ক্যাটাগরির নাম পরিবর্তন করার ফাংশন
def rewrite_category(line, new_category):
    return re.sub(r'group-title="[^"]*"', f'group-title="{new_category}"', line, flags=re.IGNORECASE)

# চ্যানেল সক্রিয় (Active) কিনা চেক করার ফাংশন
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
                
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                group_title = group_match.group(1).upper() if group_match else ""
                channel_name = line.split(",")[-1].strip().upper() if "," in line else line.upper()

                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)
                has_year = bool(YEAR_PATTERN.search(group_title)) or bool(YEAR_PATTERN.search(channel_name))
                has_season_ep = bool(SEASON_EPISODE_PATTERN.search(channel_name)) or bool(SEASON_EPISODE_PATTERN.search(group_title))

                if not is_blocked and not has_year and not has_season_ep and stream_url:
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        
                        # ১. ইসলামিক চ্যানেল
                        if any(k in group_title or k in channel_name for k in ["ISLAM", "ISLAMIC", "MADANI", "PEACE TV", "MAKKAH", "MADINAH", "SUNNAH"]):
                            updated_line = rewrite_category(line, "ISLAMIC")
                            categories["ISLAMIC"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ২. ডকুমেন্টারি চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["DISCOVERY", "NAT GEO", "NATIONAL GEOGRAPHIC", "ANIMAL PLANET", "HISTORY", "DOCUMENTARY"]):
                            updated_line = rewrite_category(line, "DOCUMENTARY")
                            categories["DOCUMENTARY"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৩. মিউজিক চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["MUSIC", "MTV", "9XM", "ZOOM", "SANGEET", "GANA", "9X"]):
                            updated_line = rewrite_category(line, "MUSIC")
                            categories["MUSIC"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৪. কিডস লাইভ চ্যানেল (যেমন Nick, Cartoon Network)
                        elif any(k in group_title or k in channel_name for k in ["CARTOON", "NICK", "POGO", "DISNEY", "SONY YAY"]):
                            updated_line = rewrite_category(line, "KIDS")
                            categories["KIDS"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৫. স্পোর্টস চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS", "WILLOW", "BEIN", "EUROSPORT", "T SPORTS", "GTV"]):
                            updated_line = rewrite_category(line, "SPORTS")
                            categories["SPORTS"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৬. বাংলাদেশ টিভি চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["BANGLA", "BANGLADESH", "BD"]):
                            updated_line = rewrite_category(line, "BANGLADESH")
                            categories["BANGLADESH"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                        # ৭. ইন্ডিয়ান চ্যানেল
                        elif any(k in group_title or k in channel_name for k in ["INDIA", "INDIAN", "HINDI", "STAR PLUS", "ZEE TV", "COLORS", "SONY SAB"]):
                            updated_line = rewrite_category(line, "INDIAN")
                            categories["INDIAN"].append((updated_line, stream_url))
                            seen_urls.add(stream_url); seen_names.add(channel_name)

                if stream_url:
                    i += 1
            i += 1

        # সমস্ত নির্বাচিত চ্যানেল একত্রিত করা
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

        # M3U ফাইল সেভ করা
        final_playlist = ["#EXTM3U"]
        for item in active_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print(f"✅ Filtered & Categorized Successfully! Total Active: {len(active_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
