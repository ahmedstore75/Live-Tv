import requests
import re

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# যেসব ক্যাটাগরি বা শব্দ থাকলে সম্পূর্ণ বাদ যাবে (Blocklist)
BLOCK_KEYWORDS = [
    "MOVIE", "MOVIES", "SERIES", "VOD", "FILM", "CINEMA", 
    "18+", "ADULT", "XXX", "PORN", "NSFW", "SEXY", "EXPLICIT"
]

try:
    print("Downloading playlist...")
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
                # চ্যানেল লিঙ্ক নেওয়া
                stream_url = lines[i + 1].strip() if (i + 1 < len(lines) and not lines[i + 1].startswith("#")) else ""
                
                # গ্রুপের নাম এবং চ্যানেলের নাম বের করা
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                group_title = group_match.group(1).upper() if group_match else ""
                
                # চ্যানেলের নাম এক্সট্র্যাক্ট করা (কমা এর পরের অংশ)
                channel_name = line.split(",")[-1].strip().upper() if "," in line else line.upper()

                # ১. ১৮+ এবং মুভি/সিরিজ ফিল্টার করা
                is_blocked = any(b_kw in group_title or b_kw in channel_name for b_kw in BLOCK_KEYWORDS)

                if not is_blocked and stream_url:
                    # ২. ডুপ্লিকেট চ্যানেল ফিল্টার (ইউআরএল বা চ্যানেল নাম ধরে)
                    if stream_url not in seen_urls and channel_name not in seen_names:
                        seen_urls.add(stream_url)
                        seen_names.add(channel_name)
                        
                        channel_block = (line, stream_url)

                        # ৩. ক্যাটাগরি অনুযায়ী ফিল্টার ও সাজানো
                        # ক. বাংলাদেশের চ্যানেল (সবার উপরে)
                        if any(bd in group_title or bd in channel_name for bd in ["BANGLA", "BANGLADESH", "BD"]):
                            bd_channels.append(channel_block)
                            
                        # খ. অল স্পোর্টস চ্যানেল (দ্বিতীয় স্থানে)
                        elif any(sp in group_title or sp in channel_name for sp in ["SPORT", "SPORTS", "CRICKET", "FOOTBALL", "TEN", "SONY", "STAR SPORTS"]):
                            sports_channels.append(channel_block)
                            
                        # গ. ইন্ডিয়া ও পাকিস্তান চ্যানেল (তৃতীয় স্থানে)
                        elif any(other in group_title or other in channel_name for other in ["INDIA", "INDIAN", "HINDI", "PUNJABI", "PAKISTAN", "PAK"]):
                            other_channels.append(channel_block)

                if stream_url:
                    i += 1
            i += 1

        # প্লেলিস্ট একত্রিত করা (বাংলাদেশ -> স্পোর্টস -> অন্যান্য)
        final_playlist = ["#EXTM3U"]
        
        for item in bd_channels + sports_channels + other_channels:
            final_playlist.append(item[0])
            final_playlist.append(item[1])

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(final_playlist))
            
        print(f"✅ Filtered successfully!")
        print(f"Total BD: {len(bd_channels)}, Sports: {len(sports_channels)}, Other: {len(other_channels)}")

except Exception as e:
    print(f"❌ Error: {e}")
