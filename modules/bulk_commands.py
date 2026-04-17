import tkinter as tk
from tkinter import ttk, messagebox
import threading
import paramiko
from pathlib import Path

class BulkCommandsModule:
    def __init__(self, parent, ssh_manager, key_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.key_manager = key_manager
        self.servers = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        # Açıklama
        tk.Label(self.frame, text="⚡ TOPLU KOMUT GÖNDERME", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(self.frame, text="Tüm sunuculara aynı anda komut gönderir (otomatik bağlanır)", font=("Arial", 9), fg="gray").pack()
        
        # Sunucu seçimi (çoklu seçim)
        select_frame = tk.LabelFrame(self.frame, text="Hedef Sunucular", padx=5, pady=5)
        select_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        self.server_listbox = tk.Listbox(select_frame, selectmode=tk.MULTIPLE, height=8, font=("Consolas", 9))
        self.server_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Butonlar
        btn_frame = tk.Frame(select_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="Tümünü Seç", command=self.select_all).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Temizle", command=self.clear_selection).pack(side=tk.LEFT, padx=2)
        
        # Komut girişi
        cmd_frame = tk.LabelFrame(self.frame, text="Komut", padx=5, pady=5)
        cmd_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.cmd_text = tk.Text(cmd_frame, height=5, font=("Consolas", 10))
        self.cmd_text.pack(fill=tk.BOTH, expand=True)
        
        # Örnek komutlar
        example_frame = tk.Frame(cmd_frame)
        example_frame.pack(fill=tk.X, pady=5)
        tk.Label(example_frame, text="Örnek:", font=("Arial", 8)).pack(side=tk.LEFT)
        
        examples = ["uptime", "df -h", "free -m", "whoami", "hostname"]
        for ex in examples:
            tk.Button(example_frame, text=ex, command=lambda e=ex: self.insert_example(e),
                     font=("Arial", 8), padx=5).pack(side=tk.LEFT, padx=2)
        
        # Gönderme butonu
        self.send_btn = tk.Button(self.frame, text="🚀 Komut Gönder", command=self.send_bulk_command,
                                   bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                   padx=20, pady=5)
        self.send_btn.pack(pady=10)
        
        # Sonuç alanı
        result_frame = tk.LabelFrame(self.frame, text="Sonuçlar", padx=5, pady=5)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Sonuç için scrollbar
        result_scroll = tk.Scrollbar(result_frame)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.result_text = tk.Text(result_frame, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9),
                                   yscrollcommand=result_scroll.set)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        result_scroll.config(command=self.result_text.yview)
        
        # İlerleme
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5, padx=5)
        
        self.status_label = tk.Label(self.frame, text="Hazır", font=("Arial", 8), fg="gray")
        self.status_label.pack()
    
    def insert_example(self, cmd):
        self.cmd_text.delete(1.0, tk.END)
        self.cmd_text.insert(1.0, cmd)
    
    def update_server_list(self, servers):
        self.servers = servers
        self.server_listbox.delete(0, tk.END)
        for server in servers:
            # Mevcut bağlantı durumunu kontrol et
            if self.ssh.is_connected(server['name']):
                status = "🔌"
            else:
                status = "⚪"
            self.server_listbox.insert(tk.END, f"{status} {server['name']} ({server['ip']})")
    
    def select_all(self):
        self.server_listbox.select_set(0, tk.END)
    
    def clear_selection(self):
        self.server_listbox.selection_clear(0, tk.END)
    
    def get_selected_servers(self):
        selected = []
        for i in self.server_listbox.curselection():
            text = self.server_listbox.get(i)
            # İkonu atla (2 karakter)
            without_icon = text[2:] if text[0] in ['🔌', '⚪'] else text
            name = without_icon.split("(")[0].strip()
            server = next((s for s in self.servers if s["name"] == name), None)
            if server:
                selected.append(server)
        return selected
    
    def connect_to_server(self, server):
        """Bir sunucuya geçici SSH bağlantısı kur"""
        key_path = Path.home() / ".ssh" / "id_ed25519"
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname=server['ip'],
                port=server['port'],
                username=server['user'],
                key_filename=str(key_path),
                timeout=10
            )
            return client
        except Exception as e:
            raise Exception(f"Bağlantı hatası: {str(e)}")
    
    def send_bulk_command(self):
        selected_servers = self.get_selected_servers()
        if not selected_servers:
            messagebox.showwarning("Uyarı", "Lütfen en az bir sunucu seçin!")
            return
        
        cmd = self.cmd_text.get("1.0", tk.END).strip()
        if not cmd:
            messagebox.showwarning("Uyarı", "Lütfen bir komut girin!")
            return
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"🚀 Komut: {cmd}\n")
        self.result_text.insert(tk.END, "=" * 70 + "\n\n")
        
        self.progress_var.set(0)
        self.send_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Komut gönderiliyor...", fg="orange")
        
        def execute():
            total = len(selected_servers)
            results = []
            
            for i, server in enumerate(selected_servers):
                self.parent.after(0, lambda s=server: self.result_text.insert(tk.END, f"📡 {s['name']} ({s['ip']}) işleniyor...\n"))
                self.parent.after(0, lambda: self.result_text.see(tk.END))
                
                client = None
                try:
                    # Önce mevcut bağlantıyı dene
                    if self.ssh.is_connected(server['name']):
                        client = self.ssh.active_connections.get(server['name'])
                    else:
                        # Yoksa yeni bağlantı kur
                        client = self.connect_to_server(server)
                    
                    # Komutu çalıştır
                    stdin, stdout, stderr = client.exec_command(cmd, timeout=30)
                    output = stdout.read().decode('utf-8', errors='ignore')
                    error = stderr.read().decode('utf-8', errors='ignore')
                    result = output + error
                    
                    if not result.strip():
                        result = "[Komut çalıştırıldı (çıktı yok)]\n"
                    
                    results.append(f"✅ {server['name']}:\n{result}\n{'-'*50}\n")
                    
                except Exception as e:
                    results.append(f"❌ {server['name']}: {str(e)}\n{'-'*50}\n")
                
                finally:
                    # Yeni kurulan bağlantıyı kapat (mevcut değilse)
                    if client and not self.ssh.is_connected(server['name']):
                        client.close()
                
                # İlerlemeyi güncelle
                progress = ((i + 1) / total) * 100
                self.parent.after(0, lambda p=progress: self.progress_var.set(p))
            
            # Tüm sonuçları göster
            for result in results:
                self.parent.after(0, lambda r=result: self.result_text.insert(tk.END, r))
            
            self.parent.after(0, lambda: self.result_text.insert(tk.END, f"\n✅ İşlem tamamlandı! {len([r for r in results if '✅' in r])}/{total} başarılı.\n"))
            self.parent.after(0, lambda: self.result_text.see(tk.END))
            self.parent.after(0, lambda: self.status_label.config(text="✅ Komut tamamlandı", fg="green"))
            self.parent.after(0, lambda: self.send_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=execute, daemon=True).start()
    
    def get_frame(self):
        return self.frame