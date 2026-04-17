import paramiko
from pathlib import Path

class SSHClientManager:
    def __init__(self):
        self.active_connections = {}
        self.key_path = Path.home() / ".ssh" / "id_ed25519"
    
    def connect(self, server):
        """Sunucuya SSH ile bağlan (şifresiz, key ile)"""
        if server['name'] in self.active_connections:
            return self.active_connections[server['name']]
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server['ip'],
            port=server['port'],
            username=server['user'],
            key_filename=str(self.key_path),
            timeout=10
        )
        self.active_connections[server['name']] = client
        return client
    
    def disconnect(self, server_name):
        """Bağlantıyı kapat"""
        if server_name in self.active_connections:
            self.active_connections[server_name].close()
            del self.active_connections[server_name]
    
    def get_sftp(self, server_name):
        """SFTP bağlantısı al"""
        client = self.active_connections.get(server_name)
        if client:
            return client.open_sftp()
        return None
    
    def is_connected(self, server_name):
        return server_name in self.active_connections