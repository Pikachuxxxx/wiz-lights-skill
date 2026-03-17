#!/usr/bin/env python3
import argparse
import subprocess
import time
import json
import hashlib
from wiz_control import WizBulb

DEFAULT_IP = "192.168.0.120"

def get_apple_music_info():
    try:
        # returns "playing, track_name, artist"
        script = 'tell application "Music" to get {player state, name of current track, artist of current track}'
        result = subprocess.check_output(['osascript', '-e', script], text=True).strip()
        parts = [p.strip() for p in result.split(',')]
        if not parts:
            return None
        
        state = parts[0]
        name = parts[1] if len(parts) > 1 else "Unknown"
        artist = parts[2] if len(parts) > 2 else "Unknown"
        
        return {
            "state": state,
            "name": name,
            "artist": artist
        }
    except Exception:
        return None

def color_from_string(s: str):
    """Generate a stable RGB based on a string (e.g. track name)."""
    h = hashlib.md5(s.encode()).digest()
    return (h[0], h[1], h[2])

def main():
    parser = argparse.ArgumentParser(description="Sync WiZ light to Apple Music (macOS)")
    parser.add_argument("--ip", default=DEFAULT_IP, help="WiZ bulb IP")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    parser.add_argument("--mode", choices=["scene", "color", "visualizer", "beat"], default="scene", help="Scene mode, unique color, visualizer pulse, or beat-sync mode")
    parser.add_argument("--scene-id", type=int, default=4, help="WiZ scene ID (4=Party, 26=Club, 23=Deepdive, 1=Ocean, 31=Rhythm)")
    parser.add_argument("--bpm", type=int, default=120, help="Target BPM for beat-sync mode (default: 120)")
    args = parser.parse_args()

    bulb = WizBulb(args.ip)
    last_track = None
    print(f"Starting Apple Music sync to {args.ip} (Mode: {args.mode}, Scene: {args.scene_id})")

    # For beat-sync and visualizer
    start_time = time.time()

    try:
        while True:
            info = get_apple_music_info()
            if not info or info["state"] != "playing":
                if last_track is not None:
                    print("Music stopped. Resetting light.")
                    bulb.set_scene(11, brightness=50) # Warm White
                    last_track = None
                time.sleep(args.interval)
                continue
            
            track_id = f"{info['name']} - {info['artist']}"

            if args.mode == "beat":
                # Beat-sync mode: rhythmic pulsing at a target BPM
                # Cycle color on every few beats
                elapsed = time.time() - start_time
                bps = args.bpm / 60.0
                beat_fraction = (elapsed * bps) % 1.0
                # Exponential brightness for a 'sharp' beat feel
                brightness = 10 + int(90 * (1.0 - beat_fraction)**3)
                
                # Change color every 4 beats
                beat_count = int(elapsed * bps)
                r, g, b = color_from_string(f"{track_id}-{beat_count // 4}")
                
                bulb.set_color(r, g, b, brightness=brightness)
                time.sleep(0.05) # Very fast polling for beat matching
                continue
            
            if args.mode == "visualizer":

            if track_id != last_track:
                print(f"Now Playing: {track_id}")
                last_track = track_id
                
                if args.mode == "scene":
                    print(f"Activating Scene {args.scene_id} for: {track_id}")
                    bulb.send({"method": "setPilot", "params": {"sceneId": args.scene_id, "speed": 100, "dimming": 100}})
                elif args.mode == "color":
                    r, g, b = color_from_string(track_id)
                    print(f"Setting unique color for: {track_id}")
                    bulb.set_color(r, g, b, brightness=100)
            
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping Apple Music sync.")

if __name__ == "__main__":
    main()
