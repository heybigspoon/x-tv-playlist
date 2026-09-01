import urllib.request
import json
import re

# --- CONFIGURATION ---
# Your specific list ID is embedded directly into the syndicate request url
LIST_ID = "1814228268662587775"
OUTPUT_FILENAME = "x_video_playlist.m3u"
# ---------------------

def extract_video_links():
    video_urls = []
    
    # Official syndicated timeline endpoint used for public embeds
    url = f"https://twimg.com{LIST_ID}&lang=en"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            # Navigate through the data structure to isolate tweets
            tweets = data.get('headers', [])
            
            for tweet in tweets:
                # Search the text payload for native video configurations
                tweet_text = json.dumps(tweet)
                
                # RegEx extraction looking for direct video content links (.mp4 or HLS variants)
                matches = re.findall(r'(https://video\.twimg\.com/[^\s"\']+\.(?:mp4|m3u8)[^\s"\']*)', tweet_text)
                for match in matches:
                    clean_match = match.replace('\\', '')
                    if clean_match not in video_urls:
                        video_urls.append(clean_match)
                        
    except Exception as e:
        print(f"Syndication request failed: {e}")
        
    return video_urls

def generate_m3u(urls):
    if not urls:
        print("No videos isolated via syndication framework. Providing placeholder.")
        with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("#EXTINF:-1, X Channel Empty - Add Video Posts To List\n")
            f.write("https://localhost/placeholder.mp4\n")
        return

    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for i, url in enumerate(urls, start=1):
            f.write(f"#EXTINF:-1 tvg-id=\"X_{i}\" tvg-name=\"X Video {i}\", X Video {i}\n")
            f.write(f"{url}\n")
            
    print(f"Success! Generated {OUTPUT_FILENAME} with {len(urls)} active streams.")

if __name__ == "__main__":
    links = extract_video_links()
    generate_m3u(links)

