from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, Response
import re
import os
import logging
import threading
import time
import subprocess
import json
import requests
from werkzeug.utils import secure_filename
from mimetypes import guess_type
import shutil
from urllib.parse import unquote
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB limit
app.config['STREAM_CHUNK_SIZE'] = 8 * 1024 * 1024  # 8MB chunks for streaming

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create downloads folder
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)

# Validate time format (HH:MM:SS or MM:SS or SS)
def validate_time(time_str):
    if not time_str:
        return True
    return re.match(r'^(\d{1,2}:)?([0-5]?\d:)?[0-5]?\d$', time_str)

# Convert time string to seconds
def time_to_seconds(time_str):
    if not time_str:
        return 0
    parts = list(map(int, time_str.split(':')))
    parts.reverse()  # Now parts are [seconds, minutes, hours] if they exist
    multipliers = [1, 60, 3600]
    seconds = 0
    for i in range(len(parts)):
        seconds += parts[i] * multipliers[i]
    return seconds

def cleanup_old_files():
    """Delete files older than 5 minutes from download folder"""
    now = time.time()
    folder = app.config['DOWNLOAD_FOLDER']
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            mtime = os.path.getmtime(file_path)
            if now - mtime > 300:  # 5 minutes in seconds
                try:
                    os.remove(file_path)
                    logging.info(f"Cleaned up old file: {filename}")
                except Exception as e:
                    logging.error(f"Error cleaning up file {filename}: {str(e)}")

# Track download status
download_status = {}
download_lock = threading.Lock()

# YouTube cookies and headers
YT_COOKIES = {
    "__Secure-3PSID": "g.a000xAi68EEwiHpVgKOgb_0IkaVhqnDZ5lzCwhQRp8c82UzZZch8f2AzQqaJKg-B05iZm6D-ygACgYKARESARASFQHGX2Mit6lAJidyakf-DSQQ3RLMZRoVAUF8yKr7g1ZnIDE3zqNE1r1J8ZOo0076",
    "__Secure-1PSIDTS": "sidts-CjIB5H03P-AdzJTCxSMrqV3MrvhaLXDlh54-abS10xB-lGChJP5JVUEZ-kj7dhf4uOxWLhAA",
    "SAPISID": "vV-FkowIK7ScWwJW/Azy3I1xFL4tE9pMHs",
    "__Secure-1PSIDCC": "AKEyXzVyk5AFJUmI0NuS3ekkFwQcPZIbC09vPY3UXHvWEGPQ_HJy3_2os9M_bTxAI20uIleCTB15",
    "SSID": "A5QQ8kH3RspqENXL5",
    "__Secure-1PAPISID": "vV-FkowIK7ScWwJW/Azy3I1xFL4tE9pMHs",
    "__Secure-1PSID": "g.a000xAi68EEwiHpVgKOgb_0IkaVhqnDZ5lzCwhQRp8c82UzZZch8TqRoD9Yv9BQP11E6lRuz6gACgYKASMSARASFQHGX2MibIOMeMIAHC47JIC3nWJAZRoVAUF8yKqHSBH9KXhliZmpeGlJWSR60076",
    "__Secure-3PAPISID": "vV-FkowIK7ScWwJW/Azy3I1xFL4tE9pMHs",
    "__Secure-3PSIDCC": "AKEyXzVSUZYWOFjQBwQTEpoRjaOdLyLsw6gZB0e4oDh_XsoQBI-8ZLZaBjqkb1Yc-kChYMVrIA",
    "__Secure-3PSIDTS": "sidts-CjIB5H03P-AdzJTCxSMrqV3MrvhaLXDlh54-abS10xB-lGChJP5JVUEZ-kj7dhf4uOxWLhAA",
    "LOGIN_INFO": "AFmmF2swRAIgSL9JJ01yt_mRAxDNK51IBdT_pHp1CXE-Jc4EZ4m6CuACIBSzAE0jJLqohH230mwp6EBAW802qnUUI2odCV0JT3yh:QUQ3MjNmeVJKVEFoVVdlbXVpRHFNTnJ1aW5DNDNqWUxwNXFSQXdRbEpRaURydVNYMW43MGxoWkdVZmozb3M2UnR6SUR3S0QtamJSZGFJQzJBOW5IMmNSb0htc3ZRdkZDdmdpZmJObTVjcFh0R2tqb1ZLUnEtRjRUcFdrUzAwSDc3Vjg3WERudnJlakViUTZ1Z29BeHIyWUtIOENBTFZJbXNR",
    "PREF": "f6=40000400&f7=4100&tz=Asia.Calcutta&f5=20000&f4=4000000"
}

YT_HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3_2 like Mac OS X;)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
    'Sec-Fetch-Mode': 'navigate',
    'X-Youtube-Client-Name': '5',
    'X-Youtube-Client-Version': '20.10.4',
    'Origin': 'https://www.youtube.com',
    'X-Goog-Visitor-Id': 'CgtneWx0QzE2MmpKWSjpibnCBjIKCgJJThIEGgAgZw%3D%3D'
}

YT_PARAMS = {'prettyPrint': 'false'}

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    # Standard URL patterns
    patterns = [
        r"youtube\.com/watch\?v=([^&]+)",         # Standard URL
        r"youtu\.be/([^?]+)",                     # Short URL
        r"youtube\.com/embed/([^/?]+)",           # Embed URL
        r"youtube\.com/v/([^/?]+)",               # Legacy URL
        r"www\.youtube\.com/live/([^/?]+)",            # Live stream URL
        r"youtube\.com/shorts/([^/?]+)",          # Shorts URL
        r"m\.youtube\.com/watch\?v=([^&]+)"       # Mobile URL
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # Try parsing as URL with query parameters
    parsed = urlparse(url)
    if parsed.hostname and ('youtube.com' in parsed.hostname or 'youtu.be' in parsed.hostname):
        if parsed.path.startswith('/watch'):
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                return qs['v'][0]
        elif parsed.path.startswith('/'):
            return parsed.path[1:].split('?')[0].split('/')[0]
    
    return None

def streams_(streams_data):
    video_streams = []
    audio_streams = []
    
    # Separate video and audio streams
    for stream in streams_data:
        mime = stream.get('mimeType', '')
        if 'video/' in mime:
            video_streams.append(stream)
        elif 'audio/' in mime and "mp4a" in mime:
            audio_streams.append(stream)
    
    # Sort video streams by resolution (descending) and bitrate (descending)
    video_streams.sort(key=lambda x: (
        x.get('width', 0) * x.get('height', 0),  # Resolution
        x.get('bitrate', 0)                      # Bitrate
    ), reverse=True)
    
    # Sort audio streams by bitrate (descending)
    audio_streams.sort(key=lambda x: x.get('bitrate', 0), reverse=True)
    
    # Select best audio (highest bitrate)
    best_audio = audio_streams[0] if audio_streams else None
    
    # Always select the highest resolution video available
    best_video = video_streams[0] if video_streams else None
                
    return best_video, best_audio

def should_reencode(video_stream):
    mime = video_stream.get('mimeType', '').lower()
    # Only re-encode if it's VP9 (webm) format
    return 'vp9' in mime or 'webm' in mime

def get_youtube_streams(video_id):
    """Get video and audio streams from YouTube API"""
    json_data = {
        'context': {
            'client': {
                'clientName': 'IOS',
                'clientVersion': '20.10.4',
                'deviceMake': 'Apple',
                'deviceModel': 'iPhone16,2',
                'userAgent': 'com.google.ios.youtube/20.10.4 (iPhone16,2; U; CPU iOS 18_3_2 like Mac OS X;)',
                'osName': 'iPhone',
                'osVersion': '18.3.2.22D82',
                'hl': 'en',
                'timeZone': 'UTC',
                'utcOffsetMinutes': 0,
            },
        },
        'videoId': video_id,
        'playbackContext': {
            'contentPlaybackContext': {
                'html5Preference': 'HTML5_PREF_WANTS',
                'signatureTimestamp': 20249,
            },
        },
        'contentCheckOk': True,
        'racyCheckOk': True,
    }
    
    response = requests.post(
        'https://www.youtube.com/youtubei/v1/player',
        params=YT_PARAMS,
        cookies=YT_COOKIES,
        headers=YT_HEADERS,
        json=json_data,
    )
    
    if response.status_code != 200:
        raise Exception(f"YouTube API request failed: {response.status_code}")
    
    data = response.json()
    streaming_data = data.get("streamingData", {})
    metadata = data.get("videoDetails", {})
    title = metadata.get("title", "YouTube Clip")
    duration  = metadata.get('lengthSeconds')
    adaptive_formats = streaming_data.get("adaptiveFormats", [])
    
    logging.error(f"Youtube Response : {data}")
    if not adaptive_formats:
        raise Exception("No adaptive formats found in YouTube response")
    
    video, audio = streams_(adaptive_formats)
    if not video or not audio:
        raise Exception("No suitable streams found")
    if should_reencode(video):
        logging.error("ENCODE  ")
        return {
            'video_url': video['url'],
            'audio_url': audio['url'],
            'duration': duration,
            'title': title,
            'encode': 1
        }
    else:
        logging.error("No ENCODE ")
        return {
            'video_url': video['url'],
            'audio_url': audio['url'],
            'duration': duration,
            'title': title,
            'encode': 0
        }
    #best_video = best_audio = None
  #  max_video = (0, 0)  # (resolution, bitrate)
 #   max_audio = 0  # bitrate
   # 
  #  for s in adaptive_formats:
   #     mime = s.get('mimeType', '')
   #     if 'video/' in mime:
   #         res = s.get('width', 0) * s.get('height', 0)
   #         br = s.get('bitrate', 0)
  #          if res > max_video[0] or (res == max_video[0] and br > max_video[1]):
  #              best_video = s
   #             max_video = (res, br)
   #     elif 'audio/' in mime and "mp4a" in mime:
   #         br = s.get('bitrate', 0)
   #         if br > max_audio:
   #             best_audio = s
   #             max_audio = br

def download_thread(link, ss, to, output, format, request_id):
    try:
        # Calculate duration
        start_sec = time_to_seconds(ss)
        end_sec = time_to_seconds(to)
        duration = end_sec - start_sec
        
        # Validate duration
        if duration > 300:
            raise Exception("Clip duration cannot exceed 5 minutes")
        
        # Update initial status
        with download_lock:
            download_status[request_id] = {
                'status': 'downloading',
                'progress': 0,
                'filename': output,
                'message': 'Getting stream info from YouTube...'
            }
        
        # Extract video ID
        video_id = extract_video_id(link)
        if not video_id:
            raise Exception("Invalid YouTube URL")
        
        # Get streams from YouTube
        streams = get_youtube_streams(video_id)
        video_url = streams['video_url']
        audio_url = streams['audio_url']
        title = streams['title']
        EncodeStatus = streams['encode']
        logging.error(f"Encode Status :  {streams['encode']}")
        
        # Generate output filename if not provided
        if not output:
            # Clean up title for filename
            base = re.sub(r'[^\w\s]', '', title).strip().replace(' ', '_')
            if not base:
                base = "clip"
            # Truncate to 50 characters
            base = base[:50]
            output = f"{base}.{format}"
        else:
            # If output has an extension, replace it with selected format
            if '.' in output:
                base = output.rsplit('.', 1)[0]
                output = f"{base}.{format}"
            else:
                output = f"{output}.{format}"
        
        # Sanitize filename
        safe_output = secure_filename(output)
        
        # Update status with final filename
        with download_lock:
            download_status[request_id]['filename'] = safe_output
        
        # Prepare output path
        output_path = os.path.join(app.config['DOWNLOAD_FOLDER'], safe_output)
        
        # Update status
        with download_lock:
            download_status[request_id]['message'] = 'Downloading...'
        logging.error(f"format :  {format}")
        if "aac" in format:
            cmd = [
                'ffmpeg',
                '-y',
                '-ss', ss,
                '-to', to,
                '-i', audio_url,
                '-c:a', 'copy',
                '-preset', 'ultrafast',
                '-movflags', '+faststart',
                output_path
            ]
        else:
            # Build FFmpeg command
            if EncodeStatus:
                cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file without asking
                    '-ss', ss,
                    '-to', to,
                    '-i', video_url,
                    '-ss', ss,
                    '-to', to,
                    '-i', audio_url,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'ultrafast',
                    '-movflags', '+faststart',
                    output_path
                ]
            else:
                cmd = [
                    'ffmpeg',
                    '-y',  # Overwrite output file without asking
                    '-ss', ss,
                    '-to', to,
                    '-i', video_url,
                    '-ss', ss,
                    '-to', to,
                    '-i', audio_url,
                    '-c', 'copy',
                    '-preset', 'ultrafast',
                    '-movflags', '+faststart',
                    output_path
                ]
        logging.error(f"Final cmd :  {cmd}")
        # Run FFmpeg command
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Monitor progress
        total_duration = duration
        time_regex = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')
        
        for line in process.stdout:
            match = time_regex.search(line)
            if match:
                hours, minutes, seconds = match.groups()
                current_sec = int(hours)*3600 + int(minutes)*60 + float(seconds)
                progress = min(100, (current_sec / total_duration) * 100)
                
                with download_lock:
                    download_status[request_id] = {
                        'status': 'downloading',
                        'progress': progress,
                        'filename': safe_output,
                        'message': f'Processing: {progress:.1f}%'
                    }
        
        process.wait()
        
        if process.returncode == 0:
            with download_lock:
                download_status[request_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'filename': safe_output,
                    'message': 'Download completed!'
                }
        else:
            raise Exception(f"FFmpeg failed with exit code {process.returncode}")
            
    except Exception as e:
        logging.error(f"Download error: {str(e)}")
        with download_lock:
            download_status[request_id] = {
                'status': 'error',
                'progress': 0,
                'filename': output if output else "clip",
                'message': f'Error: {str(e)}'
            }

@app.route("/video_info/<video_id>")
def get_video_info(video_id):
    try:
        streams = get_youtube_streams(video_id)
        return jsonify({
            "stream_url": streams['video_url'],
            "duration": int(streams['duration']),
            "title": streams['title']
        })
        
    except Exception as e:
        logging.error(f"Error getting video info: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    
    # Handle both form and JSON requests
    if request.is_json:
        data = request.get_json()
        link = data.get("link", "").strip()
        ss = data.get("ss", "").strip()
        to = data.get("to", "").strip()
        output = data.get("output", "").strip()
        format = data.get("format", "mp4").strip()
    else:
        link = request.form.get("link", "").strip()
        ss = request.form.get("ss", "").strip()
        to = request.form.get("to", "").strip()
        output = request.form.get("output", "").strip()
        format = request.form.get("format", "mp4").strip()
    
    # Validate inputs
    errors = []
    if not link:
        errors.append("Please enter a YouTube URL")
    elif not extract_video_id(link):
        errors.append("Invalid YouTube URL format")
    if not validate_time(ss):
        errors.append("Invalid start time format (use HH:MM:SS or MM:SS)")
    if not validate_time(to):
        errors.append("Invalid end time format (use HH:MM:SS or MM:SS)")
    
    # Validate format
    valid_formats = ['mp4', 'mkv', 'aac']
    if format not in valid_formats:
        format = 'mp4'  # Default to mp4 if invalid
    
    # Calculate duration in seconds
    if not errors:
        try:
            start_sec = time_to_seconds(ss) if ss else 0
            end_sec = time_to_seconds(to) if to else 300  # Default to 5 minutes
            
            if end_sec <= start_sec:
                errors.append("End time must be after start time")
            elif end_sec - start_sec > 300:
                errors.append("Clip duration cannot exceed 5 minutes")
        except Exception as e:
            errors.append(f"Error processing times: {str(e)}")
    
    if errors:
        if request.is_json:
            return jsonify({"errors": errors}), 400
        else:
            for error in errors:
                flash(error, "error")
            return redirect(url_for("index"))
    
    # Generate unique request ID
    request_id = os.urandom(16).hex()
    
    # Start download in background thread
    thread = threading.Thread(
        target=download_thread,
        args=(link, ss or "00:00:00", to or "00:05:00", output, format, request_id)
    )
    thread.start()
    
    if request.is_json:
        return jsonify({
            "request_id": request_id,
            "filename": output  # Note: This will be updated in the thread
        })
    else:
        return redirect(url_for("download_status_page", request_id=request_id))

@app.route("/stream/<filename>")
def stream_file(filename):
    safe_filename = secure_filename(filename)
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], safe_filename)
    
    if not os.path.exists(file_path):
        return "File not found", 404

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)
    
    # Determine MIME type based on file extension
    ext = os.path.splitext(filename)[1].lower()
    mime_types = {
        '.mp4': 'video/mp4',
        '.webm': 'video/webm',
        '.mkv': 'video/x-matroska'
    }
    mime_type = mime_types.get(ext, 'video/mp4')

    if not range_header:
        # Initial request - return the whole file with streaming headers
        response = Response(
            file_iterator(file_path),
            status=200,
            mimetype=mime_type,
            direct_passthrough=True
        )
        response.headers['Content-Length'] = file_size
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # Parse range header
    start, end = parse_range_header(range_header, file_size)
    content_length = end - start + 1

    # Create response with partial content
    response = Response(
        file_iterator(file_path, start, end),
        status=206,
        mimetype=mime_type,
        direct_passthrough=True
    )
    
    response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
    response.headers['Content-Length'] = content_length
    response.headers['Accept-Ranges'] = 'bytes'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

def parse_range_header(range_header, file_size):
    """Parse range header and return start/end bytes"""
    unit, ranges = range_header.split('=')
    if unit != 'bytes' or ',' in ranges:
        raise ValueError('Invalid range header')
    
    start, end = ranges.split('-')
    start = int(start) if start else 0
    end = int(end) if end else file_size - 1
    
    # Ensure end isn't beyond file size
    end = min(end, file_size - 1)
    return start, end

def file_iterator(file_path, start=None, end=None, chunk_size=1024*1024):
    """Generator function to stream file in chunks"""
    with open(file_path, 'rb') as f:
        if start is not None:
            f.seek(start)
        
        remaining = None
        if end is not None:
            remaining = end - start + 1
        
        while True:
            if remaining is not None and remaining <= 0:
                break
                
            bytes_to_read = min(chunk_size, remaining) if remaining is not None else chunk_size
            data = f.read(bytes_to_read)
            
            if not data:
                break
                
            if remaining is not None:
                remaining -= len(data)
                
            yield data
            
@app.route("/progress/<request_id>")
def download_progress(request_id):
    with download_lock:
        status = download_status.get(request_id, {
            'status': 'unknown',
            'progress': 0,
            'filename': '',
            'message': 'Request not found'
        })
    return jsonify(status)

@app.route("/download/<path:filename>")
def download_file(filename):
    # Decode URL-encoded filename
    decoded_filename = unquote(filename)
    # Get just the filename part for security
    safe_filename = secure_filename(decoded_filename.split('/')[-1])
    file_path = os.path.join(app.config['DOWNLOAD_FOLDER'], safe_filename)
    
    if not os.path.exists(file_path):
        return "File not found or has expired", 404
    
    return send_file(file_path, as_attachment=True)

def cleanup_scheduler():
    """Run cleanup every minute"""
    while True:
        cleanup_old_files()
        time.sleep(60)  # Run every minute

if __name__ == "__main__":
    # Start cleanup thread
    cleanup_thread = threading.Thread(target=cleanup_scheduler, daemon=True)
    cleanup_thread.start()
    
    port = int(os.environ.get("PORT", 9999))
    app.run(debug=True, host='0.0.0.0', port=port)
