import subprocess
from pathlib import Path
import paramiko

class KeyManager:
    def __init__(self):
        self.key_path = Path.home() / ".ssh" / "id_ed25519"
        self.pub_key_path = self.key_path.with_suffix('.pub')
    
    def ensure_key_exists(self):
        """Anahtar yoksa oluştur"""
        if not self.key_path.exists():
            self._create_key()
        return self.key_path.exists()
    
    def _create_key(self):
        (Path.home() / ".ssh").mkdir(exist_ok=True)
        cmd = f'ssh-keygen -t ed25519 -f "{self.key_path}" -N "" -C "sentinelai"'
        subprocess.run(cmd, shell=True, check=True)
    
    def get_public_key(self):
        with open(self.pub_key_path, 'r') as f:
            return f.read().strip()
    
    def upload_to_server(self, server, password):
        """SSH key'i sunucuya yükle (bir kere şifre ile)"""
        pub_key = self.get_public_key()
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server['ip'],
            port=server['port'],
            username=server['user'],
            password=password,
            timeout=10
        )
        command = f'mkdir -p ~/.ssh && echo "{pub_key}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
        client.exec_command(command)
        client.close()
        return True