
# 逻辑：
# 1. 首先连接到远程服务器。获取对应的操作系统类型。然后传输对应的exporter到远程服务器。
# 2. 检查远程服务器上是否已经有exporter在运行，如果没有则启动它。
# 3. 启动SSH隧道，将远程服务器的端口映射到本地端口。
# 4. 如果SSH连接断开，则重新连接。

import os
import sys
import subprocess
import asyncio
import asyncssh
import tomllib

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("asyncssh").setLevel(logging.CRITICAL)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class RemoteServer:
    def __init__(self, host, user, private_key, ssh_port, local_port, remote_port, name, has_gpu=None):
        self.host = host
        self.user = user
        self.port = ssh_port
        self.private_key = private_key
        self.local_port = local_port
        self.remote_port = remote_port
        self.name = name
        self.os_arch = None
        self.has_gpu = has_gpu

    def get_exporter_for_running(self):
        if self.has_gpu:
            return ['node_exporter', 'nvidia_gpu_exporter']
        else:
            return ['node_exporter']

    @classmethod
    def download_latest_exporter(cls, os_arch):
        if not os.path.exists('./exporter'):
            os.makedirs('./exporter', exist_ok=True)
        cls.download_node_exporter(os_arch)
        cls.download_nvidia_gpu_exporter(os_arch)
        logger.info("All exporters downloaded successfully.")
       

    @classmethod
    def download_clash_exporter(cls, arch='linux-amd64'):
        shell_script = "bash ./bash_scripts/download_clash_exporter.sh"
        if arch.find('darwin') > -1:
            param = 'darwin-arm64'
        elif arch.find('linux') > -1:
            param = 'linux-amd64'
        else:
            logger.error(f"Unsupported architecture: {arch}")
            return

        cmdline = f"{shell_script} {param}"
        res = subprocess.run(cmdline, shell=True, check=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to install clash exporter: {res.stderr}")
        logger.info(f"Clash exporter installed successfully for {arch} architecture.")

    @classmethod
    def download_node_exporter(cls, arch='linux-amd64'):
        shell_script = "bash ./bash_scripts/download_node_exporter.sh"
        if arch.find('darwin') > -1:
            param = 'darwin-arm64'
        elif arch.find('linux') > -1:
            param = 'linux-amd64'
        else:
            logger.error(f"Unsupported architecture: {arch}")
            return
        cmdline = f"{shell_script} {param}"
        res = subprocess.run(cmdline, shell=True, check=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to install clash exporter: {res.stderr}")
        logger.info(f"Node exporter installed successfully for {arch} architecture.")

    @classmethod
    def download_nvidia_gpu_exporter(cls, arch='linux-amd64'):
        shell_script = "bash ./bash_scripts/download_nvidia_gpu_exporter.sh"
        if arch.find('linux') > -1:
            param = 'linux_x86_64'
        else:
            logger.error(f"Unsupported architecture: {arch}")
            return
        cmdline = f"{shell_script} {param}"
        res = subprocess.run(cmdline, shell=True, check=True)
        if res.returncode != 0:
            raise RuntimeError(f"Failed to install clash exporter: {res.stderr}")
        logger.info(f"Nvidia-GPU exporter installed successfully for {arch} architecture.")

    async def upload_exporter(self):
        async with asyncssh.connect(
            self.host, port=self.port, known_hosts=None, username=self.user, client_keys=[self.private_key]
        ) as conn:
            await conn.run('mkdir -p /tmp/exporter', check=True)
            for exporter in self.get_exporter_for_running():
                cmd = f'pgrep -f "^/tmp/exporter/{exporter} "'
                result = await conn.run(cmd, check=False)
                if result.exit_status == 0:
                    logger.info(f"Exporter already running on remote server {self.name}. Skipping download.")
                    continue
                local_path = f'{BASE_DIR}/exporter/{exporter}/{self.os_arch}/{exporter}'
                remote_path = f'/tmp/exporter/{exporter}'
                await asyncssh.scp(local_path, (conn, remote_path))

    async def get_remote_os(self):
        if self.os_arch:
            return self.os_arch
        async with asyncssh.connect(
            self.host, port=self.port, username=self.user,  known_hosts=None, client_keys=[self.private_key]
        ) as conn:
            result = await conn.run("echo $(uname -s | tr '[:upper:]' '[:lower:]')-$(uname -m)", check=True)
            self.os_arch = result.stdout.strip()
            if self.os_arch == 'linux-x86_64':
                self.os_arch = 'linux-amd64'
            elif self.os_arch == 'darwin-arm64':
                self.os_arch = 'darwin-arm64'
            elif self.os_arch == 'darwin-x86_64':
                self.os_arch = 'darwin-x86_64'
            else:
                logger.error(f"Unsupported OS architecture: {self.os_arch}")
                raise RuntimeError(f"Unsupported OS architecture: {self.os_arch}")
            has_gpu = await conn.run("nvidia-smi", check=False)
            if has_gpu.exit_status == 0:
                self.has_gpu = True
            return self.os_arch

    async def check_and_start_exporter(self):
        async with asyncssh.connect(
            self.host, port=self.port, username=self.user, known_hosts=None, client_keys=[self.private_key]
        ) as conn:
            for ind, exporter in enumerate(self.get_exporter_for_running()):
                # 1. 检查是否已运行
                check_cmd = f'ps -eo args | grep "^/tmp/exporter/{exporter} " | grep -v grep'
                result = await conn.run(check_cmd, check=False)
                if result.exit_status == 0:
                    logger.info(f"{exporter} already running on remote server {self.name}. Skipping start.")
                    continue

                # 2. 启动 exporter
                start_cmd = (
                    f'nohup /tmp/exporter/{exporter} --web.listen-address=127.0.0.1:{self.remote_port+ind} '
                    f'> /tmp/{exporter}.log 2>&1 & disown'
                )
                logger.info(f"Starting exporter with cmd: {start_cmd}")
                # 用 check=False，避免异常阻塞
                await conn.run(start_cmd, check=False)
                logger.info(f"{exporter} start command sent to remote server {self.name}")

    async def start_single_tunnel(self, ind, exporter):
        while True:
            try:
                print(f"[{self.name}] starting SSH tunnel for {exporter}...")
                async with asyncssh.connect(
                    self.host, port=self.port, username=self.user, client_keys=[self.private_key]
                ) as conn:
                    local_port = self.local_port+ind
                    remote_port = self.remote_port+ind
                    listener = await conn.forward_local_port('', local_port, '127.0.0.1', remote_port)
                    await listener.wait_closed()
            except Exception as e:
                print(f"[{self.name}] SSH tunnel for {exporter} exited: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def start_ssh_tunnel(self):
        tasks = [
            asyncio.create_task(self.start_single_tunnel(ind, exporter))
            for ind, exporter in enumerate(self.get_exporter_for_running())
        ]
        await asyncio.gather(*tasks)

    async def run(self):
        # 上传exporter到远程服务器
        await self.upload_exporter()
        # 检查并启动exporter
        await self.check_and_start_exporter()
        # 打开转发的SSH隧道
        await self.start_ssh_tunnel()

async def main():
    with open("servers.toml", "rb") as f:
        config = tomllib.load(f)

    os_archs = []
    servers = []
    for server_cfg in config["servers"]:
        server = RemoteServer(
            host=server_cfg["host"],
            user=server_cfg["user"],
            private_key=server_cfg.get("private_key", "~/.ssh/id_rsa"),
            ssh_port=server_cfg.get("ssh_port", 22),
            remote_port=server_cfg.get("remote_port", 9100),
            local_port=server_cfg["local_port"],
            name=server_cfg.get("name", f'{server_cfg["user"]}@{server_cfg["host"]}'),
            has_gpu=server_cfg.get("has_gpu", None),
        )
        os_arch = await server.get_remote_os()
        os_archs.append(os_arch)
        servers.append(server)


    task = [server.run() for server in servers]
    await asyncio.gather(*task)


if __name__ == "__main__":
    asyncio.run(main())
