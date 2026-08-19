import requests

url = "https://saiptvlive.ahmed-bd-org.workers.dev/102.m3u8"

try:
    # allow_redirects=True দিয়ে ৩০২ রিডাইরেক্ট ফলো করা হচ্ছে
    response = requests.get(url, allow_redirects=True, timeout=10)
    
    if response.status_code == 200:
        with open("playlist.m3u8", "wb") as file:
            file.write(response.content)
        print("✅ Python: ডাটা সফলভাবে playlist.m3u8 ফাইলে সেভ হয়েছে!")
    else:
        print(f"❌ স্ট্যাটাস কোড: {response.status_code}")

except Exception as e:
    print(f"❌ এরর ঘটেছে: {e}")
