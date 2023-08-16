import subprocess
import re
from typing import Callable
from .consts import Protocol

port_t = tuple[int, Protocol]


def get_progress(line: str):
    rematch = re.search(r"(\d+\.\d+)% done", line)

    if rematch:
        return float(rematch.group(1))
    else:
        return None


def get_port(line: str):
    rematch = re.search(r"port (\d+)/(\w+)", line)

    if rematch:
        port = int(rematch.group(1))
        protocol = rematch.group(2)

        match protocol.lower():
            case "udp":
                return (port, Protocol.UDP)
            case "tcp":
                return (port, Protocol.TCP)
            case _:
                return (port, Protocol.UNKNOWN)
    else:
        return None


def get_ports(
    start_port: int,
    end_port: int,
    ip: str,
    nmap_xargs: str,
    set_status: Callable[[str], None],
):
    open_ports: list[port_t] = []

    process = subprocess.Popen(
        f"nmap -p{start_port}-{end_port} {ip} -vv --stats-every 2 {nmap_xargs}",
        shell=True,
        text=True,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )

    if process.stdout != None:
        for line in process.stdout:
            if line.startswith("Discovered open port"):
                port = get_port(line)

                if port:
                    open_ports.append(port)

            if "Connect Scan Timing:" in line:
                progress = get_progress(line)

                if progress:
                    set_status(f"{progress}%")

    process.wait()
    set_status("COMPLETED")

    return open_ports
