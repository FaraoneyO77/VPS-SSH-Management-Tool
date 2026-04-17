import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import re

class FirewallManagerModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.current_server = None
        self.current_zones = []
        self.current_services = []
        self.current_ports = []
        self.current_rules = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        # Başlık
        tk.Label(self.frame, text="🔥 FIREWALL YÖNETİMİ (firewalld)", 
                font=("Arial", 12, "bold"), fg="#FF5722").pack(pady=5)
        
        # Sunucu seçimi
        server_frame = tk.Frame(self.frame)
        server_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(server_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(server_frame, state="readonly", width=35)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        self.server_combo.bind("<<ComboboxSelected>>", self.load_firewall_status)
        
        self.refresh_btn = tk.Button(server_frame, text="🔄 Yenile", command=self.load_firewall_status)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Firewall durumu göstergesi
        self.status_indicator = tk.Label(server_frame, text="⚪", font=("Arial", 14))
        self.status_indicator.pack(side=tk.LEFT, padx=10)
        
        # Ana notebook (sekmeler)
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Sekme 1: Port Yönetimi (Ana)
        self.port_frame = tk.Frame(self.notebook)
        self.notebook.add(self.port_frame, text="🔌 Port Yönetimi")
        self.setup_port_tab()
        
        # Sekme 2: Zone Yönetimi
        self.zone_frame = tk.Frame(self.notebook)
        self.notebook.add(self.zone_frame, text="📦 Zone'lar")
        self.setup_zone_tab()
        
        # Sekme 3: Servis Yönetimi
        self.service_frame = tk.Frame(self.notebook)
        self.notebook.add(self.service_frame, text="🛠️ Servisler")
        self.setup_service_tab()
        
        # Sekme 4: Rich Rules (Gelişmiş Kurallar)
        self.rule_frame = tk.Frame(self.notebook)
        self.notebook.add(self.rule_frame, text="📜 Gelişmiş Kurallar")
        self.setup_rule_tab()
        
        # Sekme 5: Blacklist
        self.blacklist_frame = tk.Frame(self.notebook)
        self.notebook.add(self.blacklist_frame, text="🚫 Blacklist")
        self.setup_blacklist_tab()
        
        # Durum çubuğu
        self.status_label = tk.Label(self.frame, text="Hazır - Sunucu seçin", font=("Arial", 8), fg="gray")
        self.status_label.pack(fill=tk.X)
    
    def setup_port_tab(self):
        """Port yönetimi sekmesi - Ana özellikler burada"""
        
        # Port ekleme formu
        add_frame = tk.LabelFrame(self.port_frame, text="➕ Yeni Port Aç", padx=10, pady=10)
        add_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Port numarası
        row = 0
        tk.Label(add_frame, text="Port Numarası:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_entry = tk.Entry(add_frame, width=10)
        self.port_entry.grid(row=row, column=1, padx=5, pady=5)
        tk.Label(add_frame, text="(örn: 8080 veya 8000-8100)").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Protokol
        tk.Label(add_frame, text="Protokol:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.proto_combo = ttk.Combobox(add_frame, values=["tcp", "udp", "both"], width=8)
        self.proto_combo.current(0)
        self.proto_combo.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        # Zone
        tk.Label(add_frame, text="Zone:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.zone_combo = ttk.Combobox(add_frame, values=["public", "internal", "trusted", "home", "work"], width=12)
        self.zone_combo.current(0)
        self.zone_combo.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        # Kaynak IP (opsiyonel)
        tk.Label(add_frame, text="Kaynak IP (opsiyonel):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.source_ip_entry = tk.Entry(add_frame, width=20)
        self.source_ip_entry.grid(row=row, column=1, padx=5, pady=5)
        tk.Label(add_frame, text="(boş bırakınca herkese açık)").grid(row=row, column=2, sticky=tk.W, padx=5)
        row += 1
        
        # Kalıcı mı?
        self.permanent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(add_frame, text="Kalıcı (Permanent) - Sunucu yeniden başlasa da açık kalsın", 
                      variable=self.permanent_var).grid(row=row, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Açıklama
        tk.Label(add_frame, text="Açıklama:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.port_desc_entry = tk.Entry(add_frame, width=40)
        self.port_desc_entry.grid(row=row, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        row += 1
        
        # Buton
        tk.Button(add_frame, text="🚀 Portu Aç", command=self.add_port,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=3, pady=10)
        
        # Mevcut portlar listesi
        list_frame = tk.LabelFrame(self.port_frame, text="📋 Açık Portlar", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        columns = ("Port", "Protokol", "Zone", "Kaynak IP", "Kalıcı", "Açıklama")
        self.port_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.port_tree.heading(col, text=col)
            self.port_tree.column(col, width=100)
        
        self.port_tree.column("Port", width=80)
        self.port_tree.column("Protokol", width=70)
        self.port_tree.column("Zone", width=80)
        self.port_tree.column("Kaynak IP", width=120)
        self.port_tree.column("Kalıcı", width=60)
        self.port_tree.column("Açıklama", width=150)
        
        self.port_tree.pack(fill=tk.BOTH, expand=True)
        
        # Port işlem butonları
        btn_frame = tk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="🔒 Seçili Portu Kapat", command=self.remove_port,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📋 Seçili Portu Düzenle", command=self.edit_port,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="💾 Runtime → Permanent", command=self.permanent_save,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
    
    def setup_zone_tab(self):
        """Zone yönetimi sekmesi"""
        # Mevcut zone'lar
        tk.Label(self.zone_frame, text="Mevcut Zone'lar:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=5)
        
        self.zone_listbox = tk.Listbox(self.zone_frame, height=8, font=("Consolas", 9))
        self.zone_listbox.pack(fill=tk.X, pady=5)
        
        # Aktif zone
        tk.Label(self.zone_frame, text="Aktif Zone:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=5)
        self.active_zone_label = tk.Label(self.zone_frame, text="--", font=("Arial", 9), fg="blue")
        self.active_zone_label.pack(anchor=tk.W)
        
        # Zone işlemleri
        zone_btn_frame = tk.Frame(self.zone_frame)
        zone_btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(zone_btn_frame, text="➕ Yeni Zone Ekle", command=self.add_zone,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(zone_btn_frame, text="🎯 Default Zone Ayarla", command=self.set_default_zone,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(zone_btn_frame, text="🗑️ Zone Sil", command=self.delete_zone,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    def setup_service_tab(self):
        """Servis yönetimi sekmesi"""
        # Servis ekleme
        add_service_frame = tk.LabelFrame(self.service_frame, text="Servis Ekle", padx=5, pady=5)
        add_service_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_service_frame, text="Servis Adı:").pack(side=tk.LEFT, padx=5)
        self.service_entry = tk.Entry(add_service_frame, width=20)
        self.service_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(add_service_frame, text="Zone:").pack(side=tk.LEFT, padx=5)
        self.service_zone_combo = ttk.Combobox(add_service_frame, values=["public", "internal", "trusted"], width=10)
        self.service_zone_combo.current(0)
        self.service_zone_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Button(add_service_frame, text="➕ Ekle", command=self.add_service,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Mevcut servisler
        list_frame = tk.LabelFrame(self.service_frame, text="Mevcut Servisler", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.service_listbox = tk.Listbox(list_frame, height=10, font=("Consolas", 9))
        self.service_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Hızlı servis ekleme
        quick_frame = tk.LabelFrame(self.service_frame, text="Hızlı Ekleme", padx=5, pady=5)
        quick_frame.pack(fill=tk.X, pady=5)
        
        quick_services = ["ssh", "http", "https", "mysql", "postgresql", "redis", "docker", "kubernetes", "kube-api"]
        for i, svc in enumerate(quick_services):
            tk.Button(quick_frame, text=svc, command=lambda s=svc: self.quick_add_service(s),
                     font=("Arial", 8), width=12).grid(row=i//4, column=i%4, padx=2, pady=2)
        
        tk.Button(quick_frame, text="❌ Seçili Servisi Kaldır", command=self.remove_service,
                 bg="#f44336", fg="white").grid(row=2, column=3, padx=2, pady=2)
    
    def setup_rule_tab(self):
        """Rich Rules (Gelişmiş Kurallar) sekmesi"""
        
        # Kural ekleme formu
        add_rule_frame = tk.LabelFrame(self.rule_frame, text="➕ Yeni Kural Ekle", padx=10, pady=10)
        add_rule_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Kural tipi seçimi
        row = 0
        tk.Label(add_rule_frame, text="Kural Tipi:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rule_type_combo = ttk.Combobox(add_rule_frame, values=[
            "IP Engelle", "IP İzin", "Port Limiti", "Zamanlı Engelle", "Özel Kural"
        ], width=20)
        self.rule_type_combo.current(0)
        self.rule_type_combo.grid(row=row, column=1, padx=5, pady=5)
        self.rule_type_combo.bind("<<ComboboxSelected>>", self.on_rule_type_change)
        row += 1
        
        # IP adresi (IP Engelle/İzin için)
        tk.Label(add_rule_frame, text="IP Adresi:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rule_ip_entry = tk.Entry(add_rule_frame, width=20)
        self.rule_ip_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        # Port (Port Limiti için)
        tk.Label(add_rule_frame, text="Port:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rule_port_entry = tk.Entry(add_rule_frame, width=10)
        self.rule_port_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1
        
        # Limit (Port Limiti için)
        tk.Label(add_rule_frame, text="Limit (örn: 10/s):").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rule_limit_entry = tk.Entry(add_rule_frame, width=15)
        self.rule_limit_entry.insert(0, "10/s")
        self.rule_limit_entry.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1
        
        # Zaman aralığı (Zamanlı Engelle için)
        tk.Label(add_rule_frame, text="Zaman Aralığı:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        time_frame = tk.Frame(add_rule_frame)
        time_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        self.rule_start_hour = tk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.rule_start_hour.pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.rule_start_min = tk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.rule_start_min.pack(side=tk.LEFT)
        tk.Label(time_frame, text=" - ").pack(side=tk.LEFT)
        self.rule_end_hour = tk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.rule_end_hour.pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        self.rule_end_min = tk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.rule_end_min.pack(side=tk.LEFT)
        row += 1
        
        # Zone
        tk.Label(add_rule_frame, text="Zone:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.rule_zone_combo = ttk.Combobox(add_rule_frame, values=["public", "internal", "trusted"], width=10)
        self.rule_zone_combo.current(0)
        self.rule_zone_combo.grid(row=row, column=1, padx=5, pady=5, sticky=tk.W)
        row += 1
        
        # Kalıcı mı?
        self.rule_permanent_var = tk.BooleanVar(value=True)
        tk.Checkbutton(add_rule_frame, text="Kalıcı (Permanent)", 
                      variable=self.rule_permanent_var).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        row += 1
        
        # Özel kural metni
        tk.Label(add_rule_frame, text="Özel Kural Metni:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=5)
        self.custom_rule_text = tk.Text(add_rule_frame, height=4, width=50)
        self.custom_rule_text.grid(row=row, column=1, padx=5, pady=5)
        self.custom_rule_text.insert(tk.END, 'rule family=ipv4 source address="192.168.1.100" reject')
        self.custom_rule_text.config(state=tk.DISABLED)
        row += 1
        
        # Buton
        tk.Button(add_rule_frame, text="📜 Kural Ekle", command=self.add_rich_rule,
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=10)
        
        # Mevcut kurallar listesi
        list_frame = tk.LabelFrame(self.rule_frame, text="📋 Mevcut Kurallar", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        self.rule_listbox = tk.Listbox(list_frame, height=8, font=("Consolas", 9))
        self.rule_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        btn_frame = tk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="🗑️ Seçili Kuralı Sil", command=self.remove_rich_rule,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📋 Kuralı Göster", command=self.show_rule_detail,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
    
    def setup_blacklist_tab(self):
        """Blacklist sekmesi"""
        # Blacklist ekleme
        add_bl_frame = tk.LabelFrame(self.blacklist_frame, text="IP Engelle", padx=5, pady=5)
        add_bl_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(add_bl_frame, text="IP Adresi:").pack(side=tk.LEFT, padx=5)
        self.blacklist_ip_entry = tk.Entry(add_bl_frame, width=20)
        self.blacklist_ip_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(add_bl_frame, text="Açıklama:").pack(side=tk.LEFT, padx=5)
        self.blacklist_desc_entry = tk.Entry(add_bl_frame, width=30)
        self.blacklist_desc_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Button(add_bl_frame, text="🚫 Engelle", command=self.add_blacklist,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Blacklist listesi
        list_frame = tk.LabelFrame(self.blacklist_frame, text="Engellenen IP'ler", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("IP Adresi", "Kural", "Açıklama")
        self.blacklist_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.blacklist_tree.heading(col, text=col)
            self.blacklist_tree.column(col, width=150)
        self.blacklist_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="✅ Engeli Kaldır", command=self.remove_blacklist,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔄 Tümünü Yenile", command=self.load_blacklist,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
    
    def on_rule_type_change(self, event):
        """Kural tipi değiştiğinde form alanlarını güncelle"""
        rule_type = self.rule_type_combo.get()
        
        # Önce tüm alanları enable/disable yap
        state_ip = tk.NORMAL if rule_type in ["IP Engelle", "IP İzin"] else tk.DISABLED
        state_port = tk.NORMAL if rule_type == "Port Limiti" else tk.DISABLED
        state_limit = tk.NORMAL if rule_type == "Port Limiti" else tk.DISABLED
        state_time = tk.NORMAL if rule_type == "Zamanlı Engelle" else tk.DISABLED
        state_custom = tk.NORMAL if rule_type == "Özel Kural" else tk.DISABLED
        
        self.rule_ip_entry.config(state=state_ip)
        self.rule_port_entry.config(state=state_port)
        self.rule_limit_entry.config(state=state_limit)
        self.rule_start_hour.config(state=state_time)
        self.rule_start_min.config(state=state_time)
        self.rule_end_hour.config(state=state_time)
        self.rule_end_min.config(state=state_time)
        
        self.custom_rule_text.config(state=state_custom)
        
        # Örnek metin göster
        if rule_type == "Özel Kural":
            self.custom_rule_text.config(state=tk.NORMAL)
            self.custom_rule_text.delete(1.0, tk.END)
            self.custom_rule_text.insert(tk.END, 'rule family=ipv4 source address="192.168.1.100" reject')
            self.custom_rule_text.config(state=tk.NORMAL)
        else:
            self.custom_rule_text.config(state=tk.DISABLED)
    
    def update_server_list(self, servers):
        self.servers = servers
        self.server_combo['values'] = [f"{s['name']} ({s['ip']})" for s in servers]
        if servers:
            self.server_combo.current(0)
            self.load_firewall_status()
    
    def get_selected_server(self):
        selection = self.server_combo.get()
        if not selection:
            return None
        name = selection.split(" ")[0]
        return next((s for s in self.servers if s['name'] == name), None)
    
    def run_command(self, cmd):
        """SSH üzerinden komut çalıştır"""
        server = self.get_selected_server()
        if not server or not self.ssh.is_connected(server['name']):
            return None
        
        client = self.ssh.active_connections.get(server['name'])
        stdin, stdout, stderr = client.exec_command(cmd + " 2>/dev/null || echo 'ERROR'")
        return stdout.read().decode().strip()
    
    def load_firewall_status(self):
        """Firewall durumunu yükle"""
        server = self.get_selected_server()
        if not server:
            return
        
        if not self.ssh.is_connected(server['name']):
            self.status_indicator.config(text="⚪", fg="gray")
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        self.status_label.config(text="Firewall bilgileri yükleniyor...", fg="orange")
        self.current_server = server
        
        def load():
            # Firewall durumu
            status = self.run_command("firewall-cmd --state")
            is_running = status == "running"
            
            # Zone'lar
            zones_output = self.run_command("firewall-cmd --get-zones")
            self.current_zones = zones_output.split() if zones_output else []
            
            # Aktif zone
            active_zone = self.run_command("firewall-cmd --get-default-zone")
            
            # Servisler
            services_output = self.run_command("firewall-cmd --list-services")
            self.current_services = services_output.split() if services_output else []
            
            # Port'lar
            ports_output = self.run_command("firewall-cmd --list-ports")
            self.current_ports = ports_output.split() if ports_output else []
            
            # Rich rules
            rules_output = self.run_command("firewall-cmd --list-rich-rules")
            self.current_rules = rules_output.split('\n') if rules_output else []
            
            self.parent.after(0, lambda: self.update_ui(active_zone, is_running))
            self.parent.after(0, lambda: self.status_label.config(text="✅ Firewall durumu yüklendi", fg="green"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_ui(self, active_zone, is_running):
        """UI'ı güncelle"""
        # Durum göstergesi
        if is_running:
            self.status_indicator.config(text="🟢", fg="green")
        else:
            self.status_indicator.config(text="🔴", fg="red")
        
        self.active_zone_label.config(text=active_zone)
        
        # Zone listesi
        self.zone_listbox.delete(0, tk.END)
        for zone in self.current_zones:
            self.zone_listbox.insert(tk.END, zone)
        
        # Zone combobox'ları güncelle
        zones = self.current_zones if self.current_zones else ["public"]
        self.zone_combo['values'] = zones
        self.service_zone_combo['values'] = zones
        self.rule_zone_combo['values'] = zones
        
        # Servis listesi
        self.service_listbox.delete(0, tk.END)
        for service in self.current_services:
            self.service_listbox.insert(tk.END, service)
        
        # Port listesi
        self.port_tree.delete(*self.port_tree.get_children())
        for port in self.current_ports:
            if '/' in port:
                port_num, proto = port.split('/')
                self.port_tree.insert("", tk.END, values=(port_num, proto, "public", "0.0.0.0/0", "Evet", "-"))
        
        # Rule listesi
        self.rule_listbox.delete(0, tk.END)
        for rule in self.current_rules:
            display_rule = rule[:80] + "..." if len(rule) > 80 else rule
            self.rule_listbox.insert(tk.END, display_rule)
        
        # Blacklist yükle
        self.load_blacklist()
    
    def load_blacklist(self):
        """Blacklist'i yükle"""
        self.blacklist_tree.delete(*self.blacklist_tree.get_children())
        
        for rule in self.current_rules:
            if 'reject' in rule.lower() and 'source address' in rule.lower():
                ip_match = re.search(r'source address="([^"]+)"', rule)
                if ip_match:
                    self.blacklist_tree.insert("", tk.END, values=(ip_match.group(1), rule[:50], "-"))
    
    def add_port(self):
        """Port ekle (gelişmiş)"""
        port = self.port_entry.get().strip()
        if not port:
            messagebox.showerror("Hata", "Port numarası girin!")
            return
        
        # Port formatını kontrol et
        if not re.match(r'^\d+(-\d+)?$', port):
            messagebox.showerror("Hata", "Geçersiz port formatı! Örnek: 8080 veya 8000-8100")
            return
        
        proto = self.proto_combo.get()
        zone = self.zone_combo.get()
        source_ip = self.source_ip_entry.get().strip()
        permanent = self.permanent_var.get()
        description = self.port_desc_entry.get().strip()
        
        cmd_prefix = "firewall-cmd --permanent" if permanent else "firewall-cmd"
        
        if source_ip:
            # Kaynak IP'li port açma (rich rule ile)
            rule = f'rule family=ipv4 source address="{source_ip}" port port="{port}" protocol="{proto}" accept'
            cmd = f'{cmd_prefix} --zone={zone} --add-rich-rule="{rule}"'
        else:
            cmd = f'{cmd_prefix} --zone={zone} --add-port={port}/{proto}'
        
        self.run_command(cmd)
        
        if permanent:
            self.run_command("firewall-cmd --reload")
        
        self.status_label.config(text=f"✅ Port {port}/{proto} açıldı", fg="green")
        self.port_entry.delete(0, tk.END)
        self.source_ip_entry.delete(0, tk.END)
        self.port_desc_entry.delete(0, tk.END)
        self.load_firewall_status()
    
    def edit_port(self):
        """Port düzenle (henüz implementasyon - sil/yeniden ekle)"""
        selection = self.port_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
            return
        
        item = self.port_tree.item(selection[0])
        port = item['values'][0]
        proto = item['values'][1]
        
        if messagebox.askyesno("Port Düzenle", 
                               f"Port {port}/{proto} kapatılıp yeniden mi açılsın?\n\n"
                               f"(Düzenlemek için önce kapatıp yeni değerlerle tekrar açmalısınız)"):
            # Önce kapat
            self.run_command(f"firewall-cmd --permanent --remove-port={port}/{proto}")
            self.run_command("firewall-cmd --reload")
            # Sonra ekleme formunu doldur
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, port)
            self.proto_combo.set(proto)
            self.status_label.config(text=f"Port {port}/{proto} kapatıldı. Şimdi yeni değerlerle tekrar açabilirsiniz.", fg="orange")
            self.load_firewall_status()
    
    def remove_port(self):
        """Port kapat"""
        selection = self.port_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir port seçin!")
            return
        
        item = self.port_tree.item(selection[0])
        port = item['values'][0]
        proto = item['values'][1]
        
        if messagebox.askyesno("Port Kapat", f"Port {port}/{proto} kapatılsın mı?"):
            self.run_command(f"firewall-cmd --permanent --remove-port={port}/{proto}")
            self.run_command("firewall-cmd --reload")
            self.status_label.config(text=f"🔒 Port {port}/{proto} kapatıldı", fg="red")
            self.load_firewall_status()
    
    def add_zone(self):
        zone = simpledialog.askstring("Zone Ekle", "Zone adı girin:")
        if zone:
            self.run_command(f"firewall-cmd --permanent --new-zone={zone}")
            self.run_command("firewall-cmd --reload")
            self.load_firewall_status()
            self.status_label.config(text=f"✅ Zone {zone} eklendi", fg="green")
    
    def set_default_zone(self):
        selection = self.zone_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir zone seçin!")
            return
        zone = self.zone_listbox.get(selection[0])
        self.run_command(f"firewall-cmd --set-default-zone={zone}")
        self.load_firewall_status()
        self.status_label.config(text=f"🎯 Default zone: {zone}", fg="green")
    
    def delete_zone(self):
        selection = self.zone_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir zone seçin!")
            return
        zone = self.zone_listbox.get(selection[0])
        if messagebox.askyesno("Onay", f"'{zone}' zone'u silinsin mi?"):
            self.run_command(f"firewall-cmd --permanent --delete-zone={zone}")
            self.run_command("firewall-cmd --reload")
            self.load_firewall_status()
    
    def add_service(self):
        service = self.service_entry.get().strip()
        if not service:
            messagebox.showerror("Hata", "Servis adı girin!")
            return
        zone = self.service_zone_combo.get()
        self.run_command(f"firewall-cmd --permanent --zone={zone} --add-service={service}")
        self.run_command("firewall-cmd --reload")
        self.service_entry.delete(0, tk.END)
        self.load_firewall_status()
        self.status_label.config(text=f"✅ Servis {service} eklendi", fg="green")
    
    def quick_add_service(self, service):
        zone = "public"
        self.run_command(f"firewall-cmd --permanent --zone={zone} --add-service={service}")
        self.run_command("firewall-cmd --reload")
        self.load_firewall_status()
        self.status_label.config(text=f"✅ {service} servisi eklendi", fg="green")
    
    def remove_service(self):
        selection = self.service_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir servis seçin!")
            return
        service = self.service_listbox.get(selection[0])
        if messagebox.askyesno("Onay", f"'{service}' servisi kaldırılsın mı?"):
            zone = "public"
            self.run_command(f"firewall-cmd --permanent --zone={zone} --remove-service={service}")
            self.run_command("firewall-cmd --reload")
            self.load_firewall_status()
    
    def add_rich_rule(self):
        """Gelişmiş kural ekle"""
        rule_type = self.rule_type_combo.get()
        zone = self.rule_zone_combo.get()
        permanent = self.rule_permanent_var.get()
        
        cmd_prefix = "firewall-cmd --permanent" if permanent else "firewall-cmd"
        
        if rule_type == "Özel Kural":
            rule = self.custom_rule_text.get(1.0, tk.END).strip()
            if not rule:
                messagebox.showerror("Hata", "Kural metni girin!")
                return
        else:
            ip = self.rule_ip_entry.get().strip()
            port = self.rule_port_entry.get().strip()
            limit = self.rule_limit_entry.get().strip()
            
            if rule_type == "IP Engelle":
                if not ip:
                    messagebox.showerror("Hata", "IP adresi girin!")
                    return
                rule = f'rule family=ipv4 source address="{ip}" reject'
            
            elif rule_type == "IP İzin":
                if not ip:
                    messagebox.showerror("Hata", "IP adresi girin!")
                    return
                rule = f'rule family=ipv4 source address="{ip}" accept'
            
            elif rule_type == "Port Limiti":
                if not port:
                    messagebox.showerror("Hata", "Port numarası girin!")
                    return
                rule = f'rule family=ipv4 port port="{port}" limit value="{limit}" accept'
            
            elif rule_type == "Zamanlı Engelle":
                if not ip:
                    messagebox.showerror("Hata", "IP adresi girin!")
                    return
                start_h = self.rule_start_hour.get().zfill(2)
                start_m = self.rule_start_min.get().zfill(2)
                end_h = self.rule_end_hour.get().zfill(2)
                end_m = self.rule_end_min.get().zfill(2)
                rule = f'rule family=ipv4 source address="{ip}" time between="{start_h}:{start_m}"-"{end_h}:{end_m}" reject'
            
            else:
                return
        
        cmd = f'{cmd_prefix} --zone={zone} --add-rich-rule="{rule}"'
        self.run_command(cmd)
        
        if permanent:
            self.run_command("firewall-cmd --reload")
        
        self.status_label.config(text=f"📜 Kural eklendi: {rule[:50]}...", fg="green")
        self.load_firewall_status()
    
    def remove_rich_rule(self):
        selection = self.rule_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir kural seçin!")
            return
        rule = self.current_rules[selection[0]]
        if messagebox.askyesno("Onay", f"Kural silinsin mi?\n\n{rule[:100]}..."):
            zone = "public"
            self.run_command(f'firewall-cmd --permanent --zone={zone} --remove-rich-rule="{rule}"')
            self.run_command("firewall-cmd --reload")
            self.load_firewall_status()
            self.status_label.config(text="🗑️ Kural silindi", fg="red")
    
    def show_rule_detail(self):
        selection = self.rule_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir kural seçin!")
            return
        rule = self.current_rules[selection[0]]
        messagebox.showinfo("Kural Detayı", rule)
    
    def add_blacklist(self):
        ip = self.blacklist_ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Hata", "IP adresi girin!")
            return
        
        desc = self.blacklist_desc_entry.get().strip()
        zone = "public"
        rule = f'rule family=ipv4 source address="{ip}" reject'
        
        self.run_command(f'firewall-cmd --permanent --zone={zone} --add-rich-rule="{rule}"')
        self.run_command("firewall-cmd --reload")
        
        self.blacklist_ip_entry.delete(0, tk.END)
        self.blacklist_desc_entry.delete(0, tk.END)
        self.load_firewall_status()
        self.status_label.config(text=f"🚫 {ip} engellendi", fg="red")
    
    def remove_blacklist(self):
        selection = self.blacklist_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir IP seçin!")
            return
        
        item = self.blacklist_tree.item(selection[0])
        ip = item['values'][0]
        
        if messagebox.askyesno("Onay", f"{ip} engeli kaldırılsın mı?"):
            # Blacklist'teki kuralı bul ve sil
            for rule in self.current_rules:
                if ip in rule and 'reject' in rule.lower():
                    zone = "public"
                    self.run_command(f'firewall-cmd --permanent --zone={zone} --remove-rich-rule="{rule}"')
                    self.run_command("firewall-cmd --reload")
                    break
            
            self.load_firewall_status()
            self.status_label.config(text=f"✅ {ip} engeli kaldırıldı", fg="green")
    
    def permanent_save(self):
        self.run_command("firewall-cmd --runtime-to-permanent")
        self.status_label.config(text="💾 Tüm kurallar kalıcı olarak kaydedildi", fg="green")
        messagebox.showinfo("Başarılı", "Runtime kuralları permanent olarak kaydedildi!")
    
    def get_frame(self):
        return self.frame