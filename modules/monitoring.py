import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

class MonitoringModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.servers = []
        self.monitoring_active = False
        self.monitor_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        tk.Label(self.frame, text="📊 SUNUCU İZLEME", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Sunucu seçimi
        select_frame = tk.Frame(self.frame)
        select_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(select_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(select_frame, state="readonly", width=30)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = tk.Button(select_frame, text="🔄 Yenile", command=self.refresh_monitoring)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.auto_btn = tk.Button(select_frame, text="▶ Otomatik Yenile (5sn)", command=self.toggle_auto_refresh,
                                   bg="#4CAF50", fg="white")
        self.auto_btn.pack(side=tk.LEFT, padx=5)
        
        # Metrikler
        metrics_frame = tk.LabelFrame(self.frame, text="Sistem Metrikleri", padx=10, pady=10)
        metrics_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # CPU
        tk.Label(metrics_frame, text="CPU Kullanımı:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.cpu_label = tk.Label(metrics_frame, text="--", font=("Arial", 10))
        self.cpu_label.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.cpu_bar = ttk.Progressbar(metrics_frame, length=300, mode='determinate')
        self.cpu_bar.grid(row=0, column=2, padx=10)
        
        # RAM
        tk.Label(metrics_frame, text="RAM Kullanımı:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ram_label = tk.Label(metrics_frame, text="--", font=("Arial", 10))
        self.ram_label.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.ram_bar = ttk.Progressbar(metrics_frame, length=300, mode='determinate')
        self.ram_bar.grid(row=1, column=2, padx=10)
        
        # Disk
        tk.Label(metrics_frame, text="Disk Kullanımı:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.disk_label = tk.Label(metrics_frame, text="--", font=("Arial", 10))
        self.disk_label.grid(row=2, column=1, sticky=tk.W, pady=5)
        self.disk_bar = ttk.Progressbar(metrics_frame, length=300, mode='determinate')
        self.disk_bar.grid(row=2, column=2, padx=10)
        
        # Load Average
        tk.Label(metrics_frame, text="Load Average:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.load_label = tk.Label(metrics_frame, text="--", font=("Arial", 10))
        self.load_label.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Uptime
        tk.Label(metrics_frame, text="Çalışma Süresi:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky=tk.W, pady=5)
        self.uptime_label = tk.Label(metrics_frame, text="--", font=("Arial", 10))
        self.uptime_label.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Durum
        self.status_label = tk.Label(self.frame, text="Hazır", font=("Arial", 8), fg="gray")
        self.status_label.pack()
    
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
    
    def refresh_monitoring(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        self.status_label.config(text=f"Metrikler alınıyor: {server['name']}...", fg="orange")
        
        def get_metrics():
            client = self.ssh.active_connections.get(server['name'])
            try:
                # CPU
                stdin, stdout, stderr = client.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
                cpu = stdout.read().decode().strip()
                cpu = float(cpu) if cpu else 0
                
                # RAM
                stdin, stdout, stderr = client.exec_command("free | grep Mem | awk '{print ($3/$2) * 100}'")
                ram = float(stdout.read().decode().strip())
                
                # Disk
                stdin, stdout, stderr = client.exec_command("df -h / | tail -1 | awk '{print $5}' | tr -d '%'")
                disk = float(stdout.read().decode().strip())
                
                # Load Average
                stdin, stdout, stderr = client.exec_command("uptime | awk -F 'load average:' '{print $2}'")
                load = stdout.read().decode().strip()
                
                # Uptime
                stdin, stdout, stderr = client.exec_command("uptime | awk -F 'up' '{print $2}' | awk -F ',' '{print $1}'")
                uptime = stdout.read().decode().strip()
                
                self.parent.after(0, lambda: self.update_display(cpu, ram, disk, load, uptime))
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ Son güncelleme: {server['name']}", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(text=f"❌ Hata: {str(e)}", fg="red"))
        
        threading.Thread(target=get_metrics, daemon=True).start()
    
    def update_display(self, cpu, ram, disk, load, uptime):
        self.cpu_label.config(text=f"%{cpu:.1f}")
        self.cpu_bar['value'] = cpu
        self.cpu_bar['style'] = 'red.Horizontal.TProgressbar' if cpu > 80 else 'green.Horizontal.TProgressbar'
        
        self.ram_label.config(text=f"%{ram:.1f}")
        self.ram_bar['value'] = ram
        self.ram_bar['style'] = 'red.Horizontal.TProgressbar' if ram > 80 else 'green.Horizontal.TProgressbar'
        
        self.disk_label.config(text=f"%{disk:.1f}")
        self.disk_bar['value'] = disk
        self.disk_bar['style'] = 'red.Horizontal.TProgressbar' if disk > 80 else 'green.Horizontal.TProgressbar'
        
        self.load_label.config(text=load)
        self.uptime_label.config(text=uptime)
    
    def toggle_auto_refresh(self):
        if not self.monitoring_active:
            self.monitoring_active = True
            self.auto_btn.config(text="⏸ Durdur", bg="#f44336", fg="white")
            self.start_auto_refresh()
        else:
            self.monitoring_active = False
            self.auto_btn.config(text="▶ Otomatik Yenile (5sn)", bg="#4CAF50", fg="white")
    
    def start_auto_refresh(self):
        if self.monitoring_active:
            self.refresh_monitoring()
            self.parent.after(5000, self.start_auto_refresh)
    
    def get_frame(self):
        return self.frame