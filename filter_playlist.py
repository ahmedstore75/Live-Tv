import requests
import re

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# যেসব ক্যাটাগরি বা শব্দ থাকলে সম্পূর্ণ বাদ যাবে (Blocklist)
BLOCK_KEYWORDS = [
    # মুভি ও সিরিজ সম্পর্কিত শব্দ
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", "WEB SERIES",
    # স্ক্রিনশটের সাউথ ইন্ডিয়া, হলিউড ও অন্যান্য মুভি কিওয়ার্ড
    "SOUTH INDIA", "HOLLYWOOD", "BOLLYWOOD", "TAMIL |", "TELUGU |", 
    "KANNADA |", "MALAYALAM |", "BANGLA |", "HINDI |", "PUNJABI |",
    # এডাল্ট বা ১৮+ কনটেন্ট
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

# শাল (Years) ফিল্টার - সাল যুক্ত ক্যাটাগরিগুলো মুভির হয়ে থাকে
YEAR_PATTERN = re.compile(r'20[0-2][0-9]') # 2000 থেকে 2029 পর্যন্ত সাল ধরবে

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

                # ১. মুভি, সিরিজ, ১৮+ এবং সালযুক্ত ক্যাটাগরি ফিল্টার
                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)
                has_year = bool(YEAR_PATTERN.search(group_title)) # ক্যাটাগরিতে ২০২৪, ২০২৫, ২০২৬ জাতীয় সাল থাকলে বাদ দেবে

                if not is_blocked and not has_year and stream_url:
                    # ২. ডুপ্লিকেট চ্যানেল রিমুভ (একই চ্যানেল একবারই আসবে)
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        seen_urls.add(stream_url)
                        seen_names.add(channel_name)
                        
                        channel_block = (line, stream_url)

                        # ৩. ক্যাটাগরি ও পজিশন অনুযায়ী সাজানো
                        # ক. বাংলাদেশ লাইভ চ্যানেল (সবার উপরে)
                        if any(bd in group_title or bd in channel_name for bd in ["BANGLA", "BANGLADESH", "BD"]):
                            bd_channels.append(channel_block)
                            
                        # খ. স্পোর্টস চ্যানেল (দ্বিতীয় স্থানে)
                        elif any(sp in group_title or sp in channel_name for sp in ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS"]):
                            sports_channels.append(channel_block)
                            
                        # গ. ইন্ডিয়া ও পাকিস্তান লাইভ টিভি (তৃতীয় স্থানে)
                        elif any(other in group_title or other in channel_name for other in ["INDIA", "INDIAN", "HINDI", "PUNJABI", "PAKISTAN", "PAK"]):
                            other_channels.append(channel_block)

                if stream_url:
                    i += 1
            i += 1

        # প্লেলিস্ট তৈরি (বাংলাদেশ -> স্পোর্টস -> অন্যান্য)
        final_playlist = ["#EXTM3U"]
        for item in bd_channels + sports_channels + other_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print(f"✅ Filter Completed Successfully!")
        print(f"Stats -> BD: {len(bd_channels)}, Sports: {len(sports_channels)}, Other: {len(other_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
