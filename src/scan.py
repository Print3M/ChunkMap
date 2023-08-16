from enum import Enum
from src.scan_runner import port_t
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from pathlib import Path
import uuid

class HostStatus(Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    NOT_STARTED = "NOT_STARTED"


class Host(BaseModel):
    ip: str = ""
    uuid: UUID4 = Field(default_factory=uuid.uuid4)
    status: HostStatus = HostStatus.NOT_STARTED
    last_scanned_port: int = 0
    open_ports: list[port_t] = []
    errors: list[str] = []
    last_update: datetime


class Hosts(BaseModel):
    hosts: list[Host]

class Scan:
    hosts: Hosts = Hosts(hosts=[])
    output: Path

    def __init__(self, output: Path):
        self.output = output

    def get_hosts_to_be_scanned(self) -> list[Host]:
        # Get hosts that are not scanned yet.
        return [
            x
            for x in self.hosts.hosts
            if x.status in [HostStatus.NOT_STARTED, HostStatus.IN_PROGRESS]
        ]

    def update_host(self, host: Host):
        for i, x in enumerate(self.hosts.hosts):
            if x.ip == host.ip:
                host.last_update = datetime.now()
                self.hosts.hosts[i] = host

    def save(self):
        with open(self.output, "w") as f:
            f.write(self.hosts.model_dump_json(indent=4))

    def init_hosts(self, hosts_file: Path):
        """
        Get hosts from a raw host file and prepare schema
        in the output file.
        """
        with open(hosts_file, "r") as f:
            data = f.readlines()

        raw = [Host(ip=x.strip(), last_update=datetime.now()) for x in data]
        self.hosts = Hosts(hosts=raw)
        self.save()

    def resume_scan(self, resume_file: Path):
        """
        Get hosts from a supported schema of previous uncompleted scan.
        """
        with open(resume_file, "r") as f:
            data = f.read()

        self.hosts = Hosts.model_validate_json(data)
        self.save()