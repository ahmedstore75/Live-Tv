import requests
import re

url = "http://filex.me:8080/get.php?username=3114654477&password=5787654467&type=m3u_plus&output=ts"
headers = {"User-Agent": "IPTVSmarters/1.0.3"}

# যেসব ক্যাটাগরি বা দেশের চ্যানেল আপনি রাখতে চান
TARGET_KEYWORDS = [
    "BANGLA", "BANGLADESH", "BD", 
    "INDIA", "INDIAN", "HINDI", "PUNJABI", "TAMIL", "TELUGU",
    "PAKISTAN", "PAK", 
    "SPORTS", "SPORT", "CRICKET", "FOOTBALL"
]

try:
    print("Downloading playlist...")
    response = requests.get(url, headers=headers, timeout=60)
    
    if response.status_code == 200:
        lines = response.text.splitlines()
        filtered_playlist = ["#EXTM3U"]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("#EXTINF:"):
                # গ্রুপ টাইটেল / ক্যাটাগরি বের করা
                group_match = re.search(r'group-title="([^"]*)"', line, re.IGNORECASE)
                group_title = group_match.group(1).upper() if group_match else ""
                channel_name = line.upper()

                # VOD/Movie/Series বাদ দিয়ে শুধু কাঙ্ক্ষিত ক্যাটাগরি ফিল্টার
                if not any(vod in group_title for vod in ["MOVIE", "SERIES", "VOD", "FILM"]):
                    if any(keyword in group_title or keyword in channel_name for keyword in TARGET_KEYWORDS):
                        filtered_playlist.append(line)
                        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                            filtered_playlist.append(lines[i + 1])
                            i += 1
            i += 1

        with open("playlist.m3u8", "w", encoding="utf-8") as f:
            f.write("\n".join(filtered_playlist))
        print("✅ Filtered playlist saved successfully!")

except Exception as e:
    print(f"❌ Error: {e}")
