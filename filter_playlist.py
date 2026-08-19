import requests
import re

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# ১. যেসব শব্দ ক্যাটাগরি বা চ্যানেলে থাকলে বাদ যাবে
BLOCK_KEYWORDS = [
    # মুভি, সিরিজ ও প্ল্যাটফর্ম
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", "WEB SERIES", "MIX",
    "SONY LIV", "HOICHOI", "ZEE5", "NETFLIX", "AMAZON", "HOTSTAR", "ALT BALAJI",
    # প্রিভিয়াস স্ক্রিনশটের ক্যাটাগরি
    "SOUTH INDIA", "HOLLYWOOD", "BOLLYWOOD", "TAMIL |", "TELUGU |", 
    "KANNADA |", "MALAYALAM |", "BANGLA |", "HINDI |", "PUNJABI |",
    # এডাল্ট বা ১৮+
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

# ২. ব্র্যাকেটের ভেতরের সাল (যেমন: (2019), (2024)) বা সাধারণ সাল ধরা
YEAR_PATTERN = re.compile(r'\(?20[0-2][0-9]\)?')

# ৩. সিজন এবং এপিসোড ফিল্টার (যেমন: S01, S02, E01, EP01, EPISODE)
SEASON_EPISODE_PATTERN = re.compile(r'\b(S\d{1,2}|E\d{1,3}|EP\d{1,3}|EPISODE)\b', re.IGNORECASE)

try:
    print("Downloading and filtering playlist...")
    response = requests.get(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        lines = response.text.splitlines()
        
        bd_channels = []
        sports_channels = []
        other_channels = []
        
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

                # ফিল্টারিং শর্তসমূহ
                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)
                has_year = bool(YEAR_PATTERN.search(group_title)) or bool(YEAR_PATTERN.search(channel_name))
                has_season_ep = bool(SEASON_EPISODE_PATTERN.search(channel_name)) or bool(SEASON_EPISODE_PATTERN.search(group_title))

                # মুভি, সিরিজ, সাল ও এপিসোড না থাকলে এবং সঠিক লিঙ্ক থাকলে সেভ হবে
                if not is_blocked and not has_year and not has_season_ep and stream_url:
                    # ডুপ্লিকেট রিমুভ
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        seen_urls.add(stream_url)
                        seen_names.add(channel_name)
                        
                        channel_block = (line, stream_url)

                        # ক. বাংলাদেশ লাইভ টিভি (১ম অগ্রাধিকার)
                        if any(bd in group_title or bd in channel_name for bd in ["BANGLA", "BANGLADESH", "BD"]):
                            bd_channels.append(channel_block)
                            
                        # খ. স্পোর্টস চ্যানেল (২য় অগ্রাধিকার)
                        elif any(sp in group_title or sp in channel_name for sp in ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS"]):
                            sports_channels.append(channel_block)
                            
                        # গ. ইন্ডিয়া ও পাকিস্তান লাইভ টিভি (৩য় অগ্রাধিকার)
                        elif any(other in group_title or other in channel_name for other in ["INDIA", "INDIAN", "HINDI", "PUNJABI", "PAKISTAN", "PAK"]):
                            other_channels.append(channel_block)

                if stream_url:
                    i += 1
            i += 1

        # ফাইনাল প্লেলিস্ট মার্জিং
        final_playlist = ["#EXTM3U"]
        for item in bd_channels + sports_channels + other_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print("✅ MIX and Web-Series Successfully Filtered!")
        print(f"Stats -> BD: {len(bd_channels)}, Sports: {len(sports_channels)}, Other: {len(other_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
