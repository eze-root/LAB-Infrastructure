import os
import yaml
import time
import subprocess
import threading

def check_and_start_exporter(server):
    ssh_cmd = [
        "ssh", "-i", server["private_key"],
        f'{server["user"]}@{server["host"]}',
        f'pgrep -f node_exporter || (nohup ./node_exporter --web.listen-address=127.0.0.1:{server["remote_port"]} > node_exporter.log 2>&1 &)'
    ]
    subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def start_ssh_tunnel(server):
    ssh_cmd = [
        "ssh", "-N", "-o", "ServerAliveInterval=30", "-o", "ServerAliveCountMax=3",
        "-i", server["private_key"],
        "-L", f'0.0.0.0:{server["local_port"]}:127.0.0.1:{server["remote_port"]}',
        f'{server["user"]}@{server["host"]}'
    ]
    while True:
        print(f"[{server['name']}] starting SSH tunnel...")
        proc = subprocess.Popen(ssh_cmd)
        proc.wait()
        print(f"[{server['name']}] SSH tunnel exited. Reconnecting in 5s...")
        time.sleep(5)

def manage_server(server):
    check_and_start_exporter(server)
    start_ssh_tunnel(server)

def main():
    with open("servers.yaml", "r") as f:
        config = yaml.safe_load(f)

    for server in config["servers"]:
        t = threading.Thread(target=manage_server, args=(server,))
        t.daemon = True
        t.start()

    while True:
        time.sleep(3600)

if __name__ == "__main__":
    main()