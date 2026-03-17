import argparse
import concurrent.futures
import ipaddress
import json
import socket
import time
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_PORT = 38899


class WizBulb:
    def __init__(self, ip: str, port: int = DEFAULT_PORT, timeout: float = 1.0):
        self.ip = ip
        self.port = port
        self.timeout = timeout

    def send(self, cmd: Dict[str, Any], expect_reply: bool = True) -> Optional[Dict[str, Any]]:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.timeout)
            sock.sendto(json.dumps(cmd).encode("utf-8"), (self.ip, self.port))
            if not expect_reply:
                return None
            data, _ = sock.recvfrom(4096)
            return json.loads(data.decode("utf-8"))

    def get_status(self) -> Dict[str, Any]:
        return self.send({"method": "getPilot", "params": {}}) or {}

    def set_state(self, on: bool) -> Dict[str, Any]:
        return self.send({"method": "setPilot", "params": {"state": on}}) or {}

    def set_color(self, r: int, g: int, b: int, brightness: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"state": True, "r": int(r), "g": int(g), "b": int(b)}
        if brightness is not None:
            params["dimming"] = int(brightness)
        return self.send({"method": "setPilot", "params": params}) or {}

    def set_brightness(self, brightness: int) -> Dict[str, Any]:
        return self.send({"method": "setPilot", "params": {"dimming": int(brightness)}}) or {}

    def set_scene(self, scene_id: int, brightness: Optional[int] = None) -> Dict[str, Any]:
        params: Dict[str, Any] = {"sceneId": int(scene_id)}
        if brightness is not None:
            params["dimming"] = int(brightness)
        return self.send({"method": "setPilot", "params": params}) or {}


def local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]


def discover_wiz(subnet: Optional[str] = None, timeout: float = 0.3) -> List[Tuple[str, Dict[str, Any]]]:
    if subnet is None:
        ip = local_ip()
        net = ipaddress.ip_network(f"{ip}/24", strict=False)
    else:
        net = ipaddress.ip_network(subnet, strict=False)

    probe_msg = json.dumps({"method": "getPilot", "params": {}}).encode("utf-8")

    def probe(target_ip: str):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            try:
                s.sendto(probe_msg, (target_ip, DEFAULT_PORT))
                data, _ = s.recvfrom(4096)
                payload = json.loads(data.decode("utf-8"))
                return target_ip, payload
            except Exception:
                return None

    hosts = [str(h) for h in net.hosts()]
    found: List[Tuple[str, Dict[str, Any]]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as ex:
        for result in ex.map(probe, hosts):
            if result:
                found.append(result)
    return found


def run_demo(ip: str):
    bulb = WizBulb(ip)
    print("Using bulb:", ip)

    print("Status:", bulb.get_status())

    print("Turn ON")
    print(bulb.set_state(True))
    time.sleep(1)

    print("Set RED")
    print(bulb.set_color(255, 0, 0))
    time.sleep(1)

    print("Set brightness 25%")
    print(bulb.set_brightness(25))
    time.sleep(1)

    print("Turn OFF")
    print(bulb.set_state(False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Control a WiZ bulb over local UDP")
    parser.add_argument("--ip", help="Bulb IP address")
    parser.add_argument("--discover", action="store_true", help="Discover WiZ bulbs on local subnet")
    parser.add_argument("--subnet", help="Subnet for discovery, e.g. 192.168.0.0/24")
    parser.add_argument("--demo", action="store_true", help="Run on/red/brightness/off test")
    parser.add_argument("--scene", type=int, help="Set scene ID")
    parser.add_argument("--brightness", type=int, help="Set dimming/brightness (0-100)")
    args = parser.parse_args()

    if args.discover:
        bulbs = discover_wiz(args.subnet)
        print(json.dumps(bulbs, indent=2))
    elif args.demo:
        if not args.ip:
            raise SystemExit("--demo requires --ip")
        run_demo(args.ip)
    elif args.ip:
        bulb = WizBulb(args.ip)
        if args.scene is not None:
            print(json.dumps(bulb.set_scene(args.scene, brightness=args.brightness), indent=2))
        elif args.brightness is not None:
            print(json.dumps(bulb.set_brightness(args.brightness), indent=2))
        else:
            print(json.dumps(bulb.get_status(), indent=2))
    else:
        raise SystemExit("Provide --ip, or use --discover")
