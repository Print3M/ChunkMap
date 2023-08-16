#!/usr/bin/python3
import subprocess
from src.scan_runner import get_ports
from src.scan import Scan, HostStatus
from src.utils import check_if_file_is_empty
import sys
from rich import print
from rich.live import Live
from src.cli import ScanCli, InfoCli, print_banner, get_args, init_args, print_init_info
from rich.prompt import Confirm, Prompt


if __name__ == "__main__":
    init_args()
    print_banner()
    print_init_info()

    args = get_args()
    scan = Scan(args.output)

    if args.hosts:
        print(InfoCli.info(f"Hosts are read from the '{args.hosts}' file."))

        if not check_if_file_is_empty(args.output):
            resp = Confirm.ask(
                InfoCli.warn("Output file is not empty. Do you want to override it?")
            )

            if not resp:
                sys.exit(0)

        scan.init_hosts(args.hosts)
    elif args.resume:
        print(InfoCli.info(f"Scan from the '{args.resume}' file will be resumed."))
        scan.resume_scan(args.resume)

    hosts = scan.get_hosts_to_be_scanned()

    for n, host in enumerate(hosts):
        print("")

        try:
            with Live(refresh_per_second=4) as live:
                total = (args.last_port - host.last_scanned_port) // args.chunk
                cli = ScanCli(host=host.ip, live=live, total_chunks=total)

                for s_port in range(host.last_scanned_port, args.last_port, args.chunk):
                    e_port = s_port + args.chunk
                    s_port += 1
                    cli.add_chunk(s_port, e_port)

                    try:
                        ports = get_ports(
                            s_port, e_port, host.ip, args.xargs, cli.update_status
                        )
                        host.open_ports = sorted([*host.open_ports, *ports])
                        cli.set_ports(host.open_ports)
                    except subprocess.CalledProcessError as e:
                        host.errors.append(str(e))
                        cli.update_status("ERROR")

                    host.status = HostStatus.IN_PROGRESS
                    host.last_scanned_port = e_port
                    scan.update_host(host)
                    scan.save()
        except KeyboardInterrupt:
            print("")
            resp = Prompt.ask(
                InfoCli.warn(
                    "Mark this scan as 'completed' [red bold](c)[/red bold] or 'in_progress' [red bold](i)[/red bold] (to resume later)"
                ),
                choices=["c", "i"],
                show_choices=False,
            )
            print(resp)

            match resp:
                case "c":
                    host.status = HostStatus.COMPLETED
                case "i":
                    host.status = HostStatus.IN_PROGRESS
                case _:
                    pass

            scan.update_host(host)
            scan.save()

            continue

        host.status = HostStatus.COMPLETED
        host.last_scanned_port = 0
        scan.update_host(host)
        scan.save()
