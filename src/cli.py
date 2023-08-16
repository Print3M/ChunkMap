from rich.table import Table
from .scan import port_t
from rich.console import Group
from rich.live import Live
import argparse
from pathlib import Path
from .consts import MAX_PORT
from typing import Any
from rich import print

__args = None


def init_args():
    parser = argparse.ArgumentParser(
        prog="Nmap Runner",
        description="Progress is saved after every chunk.",
        epilog="Author: Print3M",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    parser.add_argument(
        "output",
        type=Path,
        help="Output file. In case of terminated scan, this file can be used to resume scanning state.",
    )
    group.add_argument("--hosts", type=Path, help="File with hosts (one per line).")
    group.add_argument("--resume", type=Path, help="Output file to be resumed.")
    parser.add_argument(
        "-c",
        "--chunk",
        metavar="N",
        choices=range(1, MAX_PORT),
        default=5000,
        type=int,
        help="Number of ports per chunk.",
    )
    parser.add_argument(
        "-x",
        "--xargs",
        metavar="STR",
        type=str,
        default="",
        help="String with extra Nmap arguments to be used in the scan command.",
    )
    parser.add_argument(
        "-lp",
        "--last-port",
        metavar="N",
        type=int,
        default=MAX_PORT,
        help="Port at which the scan is over.",
    )

    global __args
    __args = parser.parse_args()


def get_args() -> Any:
    return __args


def print_banner():
    banner = """
 .d8888b.  888                        888      888b     d888                   
d88P  Y88b 888                        888      8888b   d8888                   
888    888 888                        888      88888b.d88888                   
888        88888b.  888  888 88888b.  888  888 888Y88888P888  8888b.  88888b.  
888        888 "88b 888  888 888 "88b 888 .88P 888 Y888P 888     "88b 888 "88b 
888    888 888  888 888  888 888  888 888888K  888  Y8P  888 .d888888 888  888 
Y88b  d88P 888  888 Y88b 888 888  888 888 "88b 888   "   888 888  888 888 d88P 
 "Y8888P"  888  888  "Y88888 888  888 888  888 888       888 "Y888888 88888P"  
                                                                      888      
    By: Print3M                                                       888      
                                                                      888   

    """
    print(banner)


def print_init_info():
    args = get_args()
    print(InfoCli.info(f"Chunk size: {args.chunk}"))
    cmd = "nmap -p{start_port}-{end_port} {ip}" + f" {args.xargs}"
    print(InfoCli.info(f"Nmap command: {cmd}"))
    print(InfoCli.info(f"Last port: {args.last_port}"))


class ScanCli:
    live: Live
    host: str
    chunks: list[tuple[str, str]]
    total_chunks: int
    ports: list[port_t]

    def __init__(self, host: str, live: Live, total_chunks: int):
        self.host = host
        self.live = live
        self.total_chunks = total_chunks
        self.chunks = []
        self.ports = []

    def add_chunk(self, s_port: int, e_port: int, status: str = "0.00%"):
        self.chunks.append((f"{s_port}-{e_port}", status))
        self.render()

    def update_status(self, status: str):
        """
        Update status of the last chunk.
        """

        if len(self.chunks) > 0:
            # Update status in a chunk tuple
            last_chunk = list(self.chunks[-1])
            last_chunk[1] = status
            self.chunks[-1] = tuple(last_chunk)

        self.render()

    def set_ports(self, ports: list[port_t]):
        self.ports = ports
        self.render()

    def render(self):
        table = Table(title=self.host, expand=True)
        table.add_column("Id", justify="center")
        table.add_column("Chunk", style="cyan", justify="center")
        table.add_column("Status", justify="center")

        for i, row in enumerate(self.chunks):
            table.add_row(f"{i+1}/{self.total_chunks}", *row)

        group = Group(
            table, ",".join([f"{x[0]}/{x[1].value.lower()}" for x in self.ports])
        )

        self.live.update(group)


class InfoCli:
    @staticmethod
    def warn(msg: str):
        return f"[red bold][!][/red bold] {msg}"

    @staticmethod
    def info(msg: str):
        return f"[green bold][+][/green bold] {msg}"
