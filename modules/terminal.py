import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess

class TerminalModule:
    def __init__(self, parent, ssh_manager, key_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.key_manager = key_manager
        self.current_server = None
        
        self.setup_ui()
    
    def setup_ui(self):
        # Ana çerçeve
        self.frame = tk.Frame(self.parent)
        
        # Sunucu seçimi
        top_frame = tk.Frame(self.frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(top_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        
        self.connect_btn = tk.Button(top_frame, text="🔌 Terminal Bağlan", command=self.connect_terminal,
                                      bg="#4CAF50", fg="white")
        self.connect_btn.pack(side=tk.LEFT, padx=5)
        
        self.disconnect_btn = tk.Button(top_frame, text="❌ Ayır", command=self.disconnect,
                                         bg="#f44336", fg="white", state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=5)
        
        # Terminal alanı (CMD penceresi için)
        self.terminal_frame = tk.Frame(self.frame)
        self.terminal_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.terminal_text = tk.Text(self.terminal_frame, bg="#1e1e1e", fg="#d4d4d4",
                                      font=("Consolas", 10), height=20)
        self.terminal_text.pack(fill=tk.BOTH, expand=True)
        
        # Komut girişi
        cmd_frame = tk.Frame(self.frame)
        cmd_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cmd_frame, text="$>", font=("Consolas", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.cmd_entry = tk.Entry(cmd_frame, font=("Consolas", 10))
        self.cmd_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        
        tk.Button(cmd_frame, text="Gönder", command=self.send_command, bg="#555", fg="white").pack(side=tk.RIGHT, padx=5)
        
        # Durum
        self.status_label = tk.Label(self.frame, text="Hazır", font=("Arial", 8), fg="gray")
        self.status_label.pack(fill=tk.X)
    
    def update_server_list(self, servers):
        self.servers = servers
        self.server_combo['values'] = [f"{s['name']} ({s['ip']})" for s in servers]
        if servers:
            self.server_combo.current(0)
    
    def get_selected_server(self):
        selection = self.server_combo.get()
        if not selection:
            return None
        name = selection.split(" ")[0]
        return next((s for s in self.servers if s['name'] == name), None)
    
    def connect_terminal(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        self.current_server = server
        self.status_label.config(text=f"Bağlanıyor: {server['name']}...", fg="orange")
        
        def do_connect():
            try:
                # SSH bağlantısı
                client = self.ssh.connect(server)
                
                # Windows CMD terminali aç (daha doğal)
                ssh_cmd = f'ssh {server["user"]}@{server["ip"]} -p {server["port"]} -i "{self.key_manager.key_path}"'
                subprocess.Popen(f'start cmd /k "{ssh_cmd}"', shell=True)
                
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ Bağlı: {server['name']}", fg="green"))
                self.parent.after(0, lambda: self.connect_btn.config(state=tk.DISABLED))
                self.parent.after(0, lambda: self.disconnect_btn.config(state=tk.NORMAL))
                self.parent.after(0, lambda: self.terminal_text.insert(tk.END, f"\n🔌 {server['name']} bağlantısı açıldı (ayrı terminal)\n"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"Bağlantı hatası:\n{str(e)}"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ Bağlantı hatası", fg="red"))
        
        threading.Thread(target=do_connect, daemon=True).start()
    
    def send_command(self):
        if not self.ssh.is_connected(self.current_server['name']) if self.current_server else False:
            messagebox.showwarning("Uyarı", "Önce bir sunucuya bağlanın!")
            return
        
        cmd = self.cmd_entry.get()
        if not cmd:
            return
        
        self.cmd_entry.delete(0, tk.END)
        self.terminal_text.insert(tk.END, f"\n$> {cmd}\n")
        self.terminal_text.see(tk.END)
        
        client = self.ssh.active_connections.get(self.current_server['name'])
        
        def exec_cmd():
            try:
                stdin, stdout, stderr = client.exec_command(cmd, timeout=10)
                output = stdout.read().decode('utf-8', errors='ignore')
                error = stderr.read().decode('utf-8', errors='ignore')
                result = output + error
                if not result.strip():
                    result = "[Komut çalıştırıldı]\n"
                self.parent.after(0, lambda: self.terminal_text.insert(tk.END, result))
                self.parent.after(0, lambda: self.terminal_text.see(tk.END))
            except Exception as e:
                self.parent.after(0, lambda: self.terminal_text.insert(tk.END, f"Hata: {str(e)}\n"))
        
        threading.Thread(target=exec_cmd, daemon=True).start()
    
    def disconnect(self):
        if self.current_server:
            self.ssh.disconnect(self.current_server['name'])
            self.current_server = None
            self.status_label.config(text="Bağlantı kesildi", fg="gray")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.terminal_text.insert(tk.END, "\n❌ Bağlantı kesildi\n")
    
    def get_frame(self):
        return self.frame