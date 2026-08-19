import fs from 'fs';

async function saveData() {
  try {
    const response = await fetch("https://saiptvlive.ahmed-bd-org.workers.dev/102.m3u8", {
      redirect: 'follow'
    });

    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }

    const data = await response.text();
    fs.writeFileSync("playlist.m3u8", data);
    console.log("✅ Node.js: ডাটা সফলভাবে playlist.m3u8 ফাইলে সেভ হয়েছে!");
  } catch (error) {
    console.error("❌ এরর ঘটেছে:", error.message);
  }
}

saveData();
