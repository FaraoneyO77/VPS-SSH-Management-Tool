import tkinter as tk
from tkinter import ttk, messagebox
import threading
import paramiko
from pathlib import Path
from stat import S_ISDIR

class ServerTransferModule:
    def __init__(self, parent, ssh_manager, key_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.key_manager = key_manager
        self.servers = []
        
        self.source_server = None
        self.target_server = None
        self.source_path = "/root"
        self.target_path = "/root"
        
        self.selected_item = None
        self.selected_item_path = None
        self.selected_item_type = None  # "file" veya "dir"
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        # Başlık
        tk.Label(self.frame, text="🔄 SUNUCUDAN SUNUCUYA DOSYA/KLASÖR AKTARIMI", 
                font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(self.frame, text="Bir sunucudan diğerine dosya veya klasör aktarır (alt klasörlerle birlikte)", 
                font=("Arial", 9), fg="gray").pack()
        
        # Ana panel (iki taraf için)
        main_frame = tk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # ==================== SOL TARAF: KAYNAK (GÖNDEREN) ====================
        source_frame = tk.LabelFrame(main_frame, text="📤 KAYNAK SUNUCU (Gönderen)", 
                                      padx=5, pady=5, font=("Arial", 10, "bold"))
        source_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Sunucu seçimi
        tk.Label(source_frame, text="Sunucu:").pack(anchor=tk.W, pady=2)
        self.source_combo = ttk.Combobox(source_frame, state="readonly", width=35)
        self.source_combo.pack(fill=tk.X, pady=2)
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self.load_source_browser())
        
        # Yol göstergesi
        path_frame = tk.Frame(source_frame)
        path_frame.pack(fill=tk.X, pady=5)
        self.source_path_label = tk.Label(path_frame, text="📁 /root", font=("Arial", 9), fg="blue")
        self.source_path_label.pack(side=tk.LEFT)
        
        tk.Button(path_frame, text="⬆ Üst Klasör", command=self.source_go_parent,
                 bg="#FF9800", fg="white", font=("Arial", 8)).pack(side=tk.RIGHT)
        
        # Dosya gezgini
        self.source_tree = ttk.Treeview(source_frame, selectmode="browse", height=12)
        self.source_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        source_scroll = tk.Scrollbar(source_frame, orient=tk.VERTICAL, command=self.source_tree.yview)
        source_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.source_tree.configure(yscrollcommand=source_scroll.set)
        
        self.source_tree.bind("<Double-1>", self.on_source_double_click)
        
        # Seçim butonları
        select_btn_frame = tk.Frame(source_frame)
        select_btn_frame.pack(fill=tk.X, pady=5)
        
        self.select_file_btn = tk.Button(select_btn_frame, text="📄 Seçili Dosyayı Seç", 
                                          command=self.select_current_file,
                                          bg="#2196F3", fg="white", font=("Arial", 9))
        self.select_file_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        self.select_dir_btn = tk.Button(select_btn_frame, text="📁 Seçili Klasörü Seç", 
                                         command=self.select_current_directory,
                                         bg="#FF9800", fg="white", font=("Arial", 9))
        self.select_dir_btn.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Seçilen öğe bilgisi
        self.source_selected_label = tk.Label(source_frame, text="Seçilen: Hiçbiri", 
                                               font=("Arial", 9), fg="gray", bg="#f0f0f0", relief=tk.SUNKEN)
        self.source_selected_label.pack(fill=tk.X, pady=5)
        
        # ==================== SAĞ TARAF: HEDEF (ALAN) ====================
        target_frame = tk.LabelFrame(main_frame, text="📥 HEDEF SUNUCU (Alan)", 
                                      padx=5, pady=5, font=("Arial", 10, "bold"))
        target_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
        
        # Sunucu seçimi
        tk.Label(target_frame, text="Sunucu:").pack(anchor=tk.W, pady=2)
        self.target_combo = ttk.Combobox(target_frame, state="readonly", width=35)
        self.target_combo.pack(fill=tk.X, pady=2)
        self.target_combo.bind("<<ComboboxSelected>>", lambda e: self.load_target_browser())
        
        # Yol göstergesi
        target_path_frame = tk.Frame(target_frame)
        target_path_frame.pack(fill=tk.X, pady=5)
        self.target_path_label = tk.Label(target_path_frame, text="📁 /root", font=("Arial", 9), fg="blue")
        self.target_path_label.pack(side=tk.LEFT)
        
        tk.Button(target_path_frame, text="⬆ Üst Klasör", command=self.target_go_parent,
                 bg="#FF9800", fg="white", font=("Arial", 8)).pack(side=tk.RIGHT)
        
        # Dosya gezgini
        self.target_tree = ttk.Treeview(target_frame, selectmode="browse", height=12)
        self.target_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        target_scroll = tk.Scrollbar(target_frame, orient=tk.VERTICAL, command=self.target_tree.yview)
        target_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.target_tree.configure(yscrollcommand=target_scroll.set)
        
        self.target_tree.bind("<Double-1>", self.on_target_double_click)
        
        # Hedef konum bilgisi
        self.target_location_label = tk.Label(target_frame, text="Hedef Konum: /root", 
                                               font=("Arial", 9), fg="blue", bg="#f0f0f0", relief=tk.SUNKEN)
        self.target_location_label.pack(fill=tk.X, pady=5)
        
        # ==================== ALT PANEL: TRANSFER BUTONU ====================
        bottom_frame = tk.Frame(self.frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # Transfer tipi seçimi (Radio butonlar)
        transfer_type_frame = tk.Frame(bottom_frame)
        transfer_type_frame.pack(pady=5)
        
        self.transfer_type = tk.StringVar(value="file")
        
        self.file_radio = tk.Radiobutton(transfer_type_frame, text="📄 Dosya Aktar", 
                                          variable=self.transfer_type, value="file",
                                          font=("Arial", 10))
        self.file_radio.pack(side=tk.LEFT, padx=10)
        
        self.dir_radio = tk.Radiobutton(transfer_type_frame, text="📁 Klasör Aktar (Alt klasörlerle birlikte)", 
                                         variable=self.transfer_type, value="dir",
                                         font=("Arial", 10))
        self.dir_radio.pack(side=tk.LEFT, padx=10)
        
        self.transfer_btn = tk.Button(bottom_frame, text="🚀 SEÇİLEN ÖĞEYİ AKTAR", 
                                       command=self.start_transfer,
                                       bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                                       padx=30, pady=8)
        self.transfer_btn.pack(pady=5)
        
        # İlerleme çubuğu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(bottom_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Sonuç alanı
        self.result_text = tk.Text(bottom_frame, height=6, bg="#1e1e1e", fg="#00ff00", 
                                    font=("Consolas", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Durum
        self.status_label = tk.Label(self.frame, text="Hazır - Sol taraftan bir dosya/klasör seçin", 
                                      font=("Arial", 8), fg="gray")
        self.status_label.pack()
    
    def update_server_list(self, servers):
        self.servers = servers
        values = [f"{s['name']} ({s['ip']})" for s in servers]
        self.source_combo['values'] = values
        self.target_combo['values'] = values
        if servers:
            self.source_combo.current(0)
            self.target_combo.current(0 if len(servers) > 1 else 0)
    
    def get_server_from_combo(self, combo):
        selection = combo.get()
        if not selection:
            return None
        name = selection.split(" ")[0]
        return next((s for s in self.servers if s['name'] == name), None)
    
    def connect_to_server(self, server):
        """Geçici SSH bağlantısı kur"""
        key_path = Path.home() / ".ssh" / "id_ed25519"
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=server['ip'],
            port=server['port'],
            username=server['user'],
            key_filename=str(key_path),
            timeout=10
        )
        return client
    
    def load_source_browser(self):
        server = self.get_server_from_combo(self.source_combo)
        if not server:
            return
        self.source_server = server
        self.load_directory(self.source_tree, self.source_path, server, "source")
    
    def load_target_browser(self):
        server = self.get_server_from_combo(self.target_combo)
        if not server:
            return
        self.target_server = server
        self.load_directory(self.target_tree, self.target_path, server, "target")
    
    def source_go_parent(self):
        if self.source_path == "/":
            return
        parent = "/".join(self.source_path.rstrip('/').split('/')[:-1])
        if not parent:
            parent = "/"
        self.source_path = parent
        self.load_directory(self.source_tree, self.source_path, self.source_server, "source")
    
    def target_go_parent(self):
        if self.target_path == "/":
            return
        parent = "/".join(self.target_path.rstrip('/').split('/')[:-1])
        if not parent:
            parent = "/"
        self.target_path = parent
        self.load_directory(self.target_tree, self.target_path, self.target_server, "target")
        self.target_location_label.config(text=f"Hedef Konum: {self.target_path}")
    
    def load_directory(self, tree, path, server, side):
        if not server:
            return
        
        if side == "source":
            self.source_path_label.config(text=f"📁 {path}")
        else:
            self.target_path_label.config(text=f"📁 {path}")
        
        def load():
            try:
                if self.ssh.is_connected(server['name']):
                    client = self.ssh.active_connections.get(server['name'])
                    sftp = client.open_sftp()
                else:
                    client = self.connect_to_server(server)
                    sftp = client.open_sftp()
                
                items = sftp.listdir_attr(path)
                
                self.parent.after(0, lambda: tree.delete(*tree.get_children()))
                
                # Önce klasörler, sonra dosyalar
                dirs = []
                files = []
                for item in items:
                    name = item.filename
                    if name in ['.', '..']:
                        continue
                    if S_ISDIR(item.st_mode):
                        dirs.append(item)
                    else:
                        files.append(item)
                
                # Üst klasör (root değilse)
                if path != "/":
                    self.parent.after(0, lambda: tree.insert("", "end", text="📁 ..", values=("parent", "")))
                
                # Klasörleri ekle
                for item in sorted(dirs, key=lambda x: x.filename):
                    name = item.filename
                    self.parent.after(0, lambda n=name: tree.insert("", "end", text=f"📁 {n}", values=("dir", n)))
                
                # Dosyaları ekle
                for item in sorted(files, key=lambda x: x.filename):
                    name = item.filename
                    size = self.format_size(item.st_size)
                    self.parent.after(0, lambda n=name, s=size: tree.insert("", "end", text=f"📄 {n}", values=("file", n, s)))
                
                sftp.close()
                if not self.ssh.is_connected(server['name']):
                    client.close()
                    
            except Exception as e:
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"Hata: {str(e)}\n"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def get_current_selection(self):
        """Mevcut seçili öğeyi döndürür"""
        selected = self.source_tree.selection()
        if not selected:
            return None, None, None
        
        item = self.source_tree.item(selected[0])
        text = item['text']
        values = item['values']
        
        if not values:
            return None, None, None
        
        if ".." in text:
            return None, None, None
        
        item_type = values[0]
        item_name = values[1] if len(values) > 1 else text.split(" ", 1)[1] if " " in text else text
        item_path = f"{self.source_path}/{item_name}".replace("//", "/")
        
        return item_name, item_path, item_type
    
    def select_current_file(self):
        """Mevcut seçili dosyayı seç"""
        name, path, item_type = self.get_current_selection()
        if not name:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden bir dosya seçin!")
            return
        
        if item_type != "file":
            messagebox.showwarning("Uyarı", "Bu bir dosya değil! Lütfen 'Klasör Seç' butonunu kullanın veya bir dosya seçin.")
            return
        
        self.selected_item = name
        self.selected_item_path = path
        self.selected_item_type = "file"
        self.source_selected_label.config(text=f"✅ Seçilen DOSYA: {name}", fg="green", bg="#e8f5e9")
        self.status_label.config(text=f"✅ Dosya seçildi: {name}", fg="green")
        self.result_text.insert(tk.END, f"📄 Dosya seçildi: {path}\n")
        self.result_text.see(tk.END)
        self.transfer_type.set("file")
    
    def select_current_directory(self):
        """Mevcut seçili klasörü seç"""
        name, path, item_type = self.get_current_selection()
        if not name:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden bir klasör seçin!")
            return
        
        if item_type != "dir":
            messagebox.showwarning("Uyarı", "Bu bir klasör değil! Lütfen 'Dosya Seç' butonunu kullanın veya bir klasör seçin.")
            return
        
        self.selected_item = name
        self.selected_item_path = path
        self.selected_item_type = "dir"
        self.source_selected_label.config(text=f"✅ Seçilen KLASÖR: {name}", fg="green", bg="#e8f5e9")
        self.status_label.config(text=f"✅ Klasör seçildi: {name}", fg="green")
        self.result_text.insert(tk.END, f"📁 Klasör seçildi: {path}\n")
        self.result_text.see(tk.END)
        self.transfer_type.set("dir")
    
    def on_source_double_click(self, event):
        """Çift tıklama ile klasör içine gir, dosya seçme (buton kullanılacak)"""
        selected = self.source_tree.selection()
        if not selected:
            return
        
        item = self.source_tree.item(selected[0])
        text = item['text']
        values = item['values']
        
        if not values:
            return
        
        if ".." in text:
            self.source_go_parent()
            return
        
        item_type = values[0]
        item_name = values[1] if len(values) > 1 else text.split(" ", 1)[1] if " " in text else text
        
        if item_type == "dir":
            # Klasör: içine gir
            new_path = f"{self.source_path}/{item_name}".replace("//", "/")
            self.source_path = new_path
            self.load_directory(self.source_tree, self.source_path, self.source_server, "source")
        # Dosyaya çift tıklama artık seçmiyor, buton kullanılacak
    
    def on_target_double_click(self, event):
        selected = self.target_tree.selection()
        if not selected:
            return
        
        item = self.target_tree.item(selected[0])
        text = item['text']
        values = item['values']
        
        if not values:
            return
        
        if ".." in text:
            self.target_go_parent()
            return
        
        item_type = values[0]
        item_name = values[1] if len(values) > 1 else text.split(" ", 1)[1] if " " in text else text
        
        if item_type == "dir":
            # Klasör: içine gir
            new_path = f"{self.target_path}/{item_name}".replace("//", "/")
            self.target_path = new_path
            self.load_directory(self.target_tree, self.target_path, self.target_server, "target")
            self.target_location_label.config(text=f"Hedef Konum: {self.target_path}")
    
    def start_transfer(self):
        if not self.selected_item:
            messagebox.showwarning("Uyarı", "Lütfen önce kaynak sunucudan bir dosya veya klasör seçin!\n\n(Listeden öğeyi seçip 'Seçili Dosyayı Seç' veya 'Seçili Klasörü Seç' butonuna tıklayın)")
            return
        
        source_server = self.get_server_from_combo(self.source_combo)
        target_server = self.get_server_from_combo(self.target_combo)
        
        if not source_server or not target_server:
            messagebox.showwarning("Uyarı", "Lütfen kaynak ve hedef sunucuyu seçin!")
            return
        
        if source_server['name'] == target_server['name']:
            messagebox.showwarning("Uyarı", "Kaynak ve hedef sunucu aynı olamaz!")
            return
        
        transfer_mode = self.transfer_type.get()
        
        # Seçilen öğe ile transfer tipi uyumlu mu kontrol et
        if transfer_mode == "file" and self.selected_item_type == "dir":
            messagebox.showerror("Hata", 
                               f"Seçili öğe bir KLASÖR: '{self.selected_item}'\n"
                               f"Klasör aktarmak için 'Klasör Aktar' seçeneğini işaretleyin veya\n"
                               f"'Seçili Klasörü Seç' butonunu kullanın.")
            return
        
        elif transfer_mode == "dir" and self.selected_item_type == "file":
            messagebox.showerror("Hata", 
                               f"Seçili öğe bir DOSYA: '{self.selected_item}'\n"
                               f"Dosya aktarmak için 'Dosya Aktar' seçeneğini işaretleyin veya\n"
                               f"'Seçili Dosyayı Seç' butonunu kullanın.")
            return
        
        dest_path = f"{self.target_path}/{self.selected_item}".replace("//", "/")
        
        self.result_text.insert(tk.END, "\n" + "=" * 50 + "\n")
        if transfer_mode == "file":
            self.result_text.insert(tk.END, f"🚀 DOSYA AKTARIMI BAŞLIYOR\n")
        else:
            self.result_text.insert(tk.END, f"🚀 KLASÖR AKTARIMI BAŞLIYOR (Alt klasörlerle)\n")
        self.result_text.insert(tk.END, f"   Kaynak: {source_server['name']}:{self.selected_item_path}\n")
        self.result_text.insert(tk.END, f"   Hedef: {target_server['name']}:{dest_path}\n")
        self.result_text.see(tk.END)
        
        self.transfer_btn.config(state=tk.DISABLED)
        self.file_radio.config(state=tk.DISABLED)
        self.dir_radio.config(state=tk.DISABLED)
        self.select_file_btn.config(state=tk.DISABLED)
        self.select_dir_btn.config(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_label.config(text="Aktarım yapılıyor...", fg="orange")
        
        def transfer():
            try:
                # Kaynak bağlantı
                if self.ssh.is_connected(source_server['name']):
                    source_client = self.ssh.active_connections.get(source_server['name'])
                    close_source = False
                else:
                    source_client = self.connect_to_server(source_server)
                    close_source = True
                
                # Hedef bağlantı
                if self.ssh.is_connected(target_server['name']):
                    target_client = self.ssh.active_connections.get(target_server['name'])
                    close_target = False
                else:
                    target_client = self.connect_to_server(target_server)
                    close_target = True
                
                source_sftp = source_client.open_sftp()
                target_sftp = target_client.open_sftp()
                
                if transfer_mode == "file":
                    # Dosya aktarımı
                    file_size = source_sftp.stat(self.selected_item_path).st_size
                    
                    with source_sftp.open(self.selected_item_path, 'rb') as src:
                        with target_sftp.open(dest_path, 'wb') as dst:
                            transferred = 0
                            data = src.read(1024 * 1024)
                            while data:
                                dst.write(data)
                                transferred += len(data)
                                progress = (transferred / file_size) * 100
                                self.parent.after(0, lambda p=progress: self.progress_var.set(p))
                                data = src.read(1024 * 1024)
                    
                    self.parent.after(0, lambda: self.result_text.insert(tk.END, f"✅ Dosya aktarımı başarılı! ({self.format_size(file_size)})\n"))
                
                else:
                    # Klasör aktarımı (recursive)
                    total_size = self.transfer_directory(source_sftp, target_sftp, 
                                                          self.selected_item_path, dest_path)
                    self.parent.after(0, lambda: self.result_text.insert(tk.END, f"✅ Klasör aktarımı başarılı! Toplam: {self.format_size(total_size)}\n"))
                
                source_sftp.close()
                target_sftp.close()
                
                if close_source:
                    source_client.close()
                if close_target:
                    target_client.close()
                
                self.parent.after(0, lambda: self.status_label.config(text="✅ Aktarım tamamlandı", fg="green"))
                self.parent.after(0, lambda: self.progress_var.set(100))
                
                # Hedef gezgini yenile
                self.parent.after(1000, lambda: self.load_target_browser())
                
            except Exception as e:
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"❌ Aktarım hatası: {str(e)}\n"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ Aktarım hatası", fg="red"))
            finally:
                self.parent.after(0, lambda: self.transfer_btn.config(state=tk.NORMAL))
                self.parent.after(0, lambda: self.file_radio.config(state=tk.NORMAL))
                self.parent.after(0, lambda: self.dir_radio.config(state=tk.NORMAL))
                self.parent.after(0, lambda: self.select_file_btn.config(state=tk.NORMAL))
                self.parent.after(0, lambda: self.select_dir_btn.config(state=tk.NORMAL))
        
        threading.Thread(target=transfer, daemon=True).start()
    
    def transfer_directory(self, source_sftp, target_sftp, source_path, dest_path):
        """Klasör ve içeriğini recursive aktar"""
        total_size = 0
        
        # Hedefte klasörü oluştur
        try:
            target_sftp.mkdir(dest_path)
        except:
            pass  # Zaten varsa hata verme
        
        # Kaynak klasördeki öğeleri listele
        items = source_sftp.listdir_attr(source_path)
        
        for item in items:
            name = item.filename
            if name in ['.', '..']:
                continue
            
            src_item = f"{source_path}/{name}".replace("//", "/")
            dst_item = f"{dest_path}/{name}".replace("//", "/")
            
            if S_ISDIR(item.st_mode):
                # Alt klasör
                total_size += self.transfer_directory(source_sftp, target_sftp, src_item, dst_item)
            else:
                # Dosya
                with source_sftp.open(src_item, 'rb') as src:
                    with target_sftp.open(dst_item, 'wb') as dst:
                        data = src.read(1024 * 1024)
                        while data:
                            dst.write(data)
                            total_size += len(data)
                            data = src.read(1024 * 1024)
        
        return total_size
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def get_frame(self):
        return self.frame