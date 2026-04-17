import tkinter as tk
from tkinter import ttk, messagebox
import threading

class ServiceManagerModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.servers = []
        self.current_services = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        tk.Label(self.frame, text="🛠️ SERVİS YÖNETİMİ", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Kontroller
        control_frame = tk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(control_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(control_frame, state="readonly", width=25)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        self.server_combo.bind("<<ComboboxSelected>>", lambda e: self.list_services())
        
        self.refresh_btn = tk.Button(control_frame, text="🔄 Servisleri Listele", command=self.list_services)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Arama
        tk.Label(control_frame, text="Ara:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(control_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_services())
        
        # Servis listesi
        list_frame = tk.LabelFrame(self.frame, text="Servisler", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        columns = ("Servis", "Durum", "Aktif", "Açıklama")
        self.service_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)
        self.service_tree.heading("#0", text="")
        self.service_tree.heading("Servis", text="Servis Adı")
        self.service_tree.heading("Durum", text="Durum")
        self.service_tree.heading("Aktif", text="Aktif")
        self.service_tree.heading("Açıklama", text="Açıklama")
        self.service_tree.column("#0", width=0, stretch=False)
        self.service_tree.column("Servis", width=200)
        self.service_tree.column("Durum", width=100)
        self.service_tree.column("Aktif", width=100)
        self.service_tree.column("Açıklama", width=250)
        self.service_tree.pack(fill=tk.BOTH, expand=True)
        
        # Servis butonları
        btn_frame = tk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.start_btn = tk.Button(btn_frame, text="▶ Başlat", command=lambda: self.service_action("start"), bg="#4CAF50", fg="white")
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Durdur", command=lambda: self.service_action("stop"), bg="#f44336", fg="white")
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        self.restart_btn = tk.Button(btn_frame, text="🔄 Yeniden Başlat", command=lambda: self.service_action("restart"), bg="#FF9800", fg="white")
        self.restart_btn.pack(side=tk.LEFT, padx=2)
        
        self.enable_btn = tk.Button(btn_frame, text="✅ Enable", command=lambda: self.service_action("enable"), bg="#2196F3", fg="white")
        self.enable_btn.pack(side=tk.LEFT, padx=2)
        
        self.disable_btn = tk.Button(btn_frame, text="❌ Disable", command=lambda: self.service_action("disable"), bg="#9C27B0", fg="white")
        self.disable_btn.pack(side=tk.LEFT, padx=2)
        
        self.status_btn = tk.Button(btn_frame, text="📋 Durum", command=lambda: self.service_action("status"), bg="#607D8B", fg="white")
        self.status_btn.pack(side=tk.LEFT, padx=2)
        
        # Sonuç alanı
        result_frame = tk.LabelFrame(self.frame, text="Sonuç", padx=5, pady=5)
        result_frame.pack(fill=tk.X, pady=5, padx=5)
        
        self.result_text = tk.Text(result_frame, height=5, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
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
    
    def list_services(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        self.status_label.config(text=f"Servisler listeleniyor: {server['name']}...", fg="orange")
        
        def list_thread():
            client = self.ssh.active_connections.get(server['name'])
            try:
                stdin, stdout, stderr = client.exec_command("systemctl list-units --type=service --all --no-pager --no-legend")
                output = stdout.read().decode('utf-8', errors='ignore')
                
                services = []
                for line in output.split('\n'):
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        service_name = parts[0]
                        load = parts[1]
                        active = parts[2]
                        status = parts[3]
                        description = ' '.join(parts[4:]) if len(parts) > 4 else ''
                        
                        status_icon = "🟢" if active == "active" else "🔴" if active == "failed" else "⚪"
                        services.append({
                            'name': service_name,
                            'status': f"{status_icon} {status}",
                            'active': active,
                            'description': description[:50]
                        })
                
                self.current_services = services
                self.parent.after(0, self.filter_services)
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ {len(services)} servis listelendi", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(text=f"❌ Hata: {str(e)}", fg="red"))
        
        threading.Thread(target=list_thread, daemon=True).start()
    
    def filter_services(self):
        search_term = self.search_entry.get().lower()
        self.service_tree.delete(*self.service_tree.get_children())
        
        for service in self.current_services:
            if search_term in service['name'].lower() or search_term in service['description'].lower():
                self.service_tree.insert("", tk.END, values=(
                    service['name'],
                    service['status'],
                    service['active'],
                    service['description']
                ))
    
    def service_action(self, action):
        selected = self.service_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir servis seçin!")
            return
        
        item = self.service_tree.item(selected[0])
        service_name = item['values'][0]
        
        server = self.get_selected_server()
        if not server:
            return
        
        action_names = {"start": "Başlat", "stop": "Durdur", "restart": "Yeniden Başlat", 
                        "enable": "Enable", "disable": "Disable", "status": "Durum"}
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"🔄 {action_names[action]} yapılıyor: {service_name}\n")
        
        def action_thread():
            client = self.ssh.active_connections.get(server['name'])
            try:
                stdin, stdout, stderr = client.exec_command(f"sudo systemctl {action} {service_name} 2>&1")
                output = stdout.read().decode('utf-8', errors='ignore')
                error = stderr.read().decode('utf-8', errors='ignore')
                result = output + error
                
                self.parent.after(0, lambda: self.result_text.insert(tk.END, result if result else "✅ İşlem tamamlandı\n"))
                self.parent.after(0, self.list_services)  # Listeyi yenile
            except Exception as e:
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"❌ Hata: {str(e)}\n"))
        
        threading.Thread(target=action_thread, daemon=True).start()
    
    def get_frame(self):
        return self.frame