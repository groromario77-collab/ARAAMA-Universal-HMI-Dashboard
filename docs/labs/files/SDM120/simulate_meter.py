"""Read-only teaching meter: python simulate_meter.py --bind YOUR_COMPUTER_LAN_IP"""
import argparse
import socketserver
import struct


class Meter(socketserver.StreamRequestHandler):
    def handle(self):
        self.connection.settimeout(30)
        while header := self.rfile.read(7):
            if len(header) != 7:
                return
            transaction, protocol, length, unit = struct.unpack(">HHHB", header)
            if protocol != 0 or not 2 <= length <= 254:
                return
            request = self.rfile.read(length - 1)
            if len(request) != length - 1:
                return
            if unit != 1:
                continue
            if request == bytes.fromhex("04 00 0C 00 02"):
                response = bytes([4, 4]) + struct.pack(">f", self.server.watts)
            else:
                error = 2 if request[0] == 4 else 1
                response = bytes([request[0] | 128, error])
            self.wfile.write(struct.pack(">HHHB", transaction, 0, len(response) + 1, unit) + response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serve one SDM120 input value on Modbus TCP, Unit ID 1.")
    parser.add_argument("--bind", default="127.0.0.1", help="Set the computer's LAN address for a tablet on the same network.")
    parser.add_argument("--port", type=int, default=1502)
    parser.add_argument("--watts", type=float, default=720)
    options = parser.parse_args()
    with socketserver.ThreadingTCPServer((options.bind, options.port), Meter) as server:
        server.daemon_threads = True
        server.watts = options.watts
        print(f"Modbus TCP {options.bind}:{options.port}, unit 1, input 12, {server.watts:g} W", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
