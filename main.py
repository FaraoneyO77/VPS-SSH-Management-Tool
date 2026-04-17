import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
from pathlib import Path

# Core
from core.ssh_client import SSHClientManager
from core.key_manager import KeyManager

# Modüller
from modules.terminal import TerminalModule
from modules.file_browser import FileBrowserModule
from modules.file_transfer import FileTransferModule
from modules.bulk_commands import BulkCommandsModule
from modules.monitoring import MonitoringModule
from modules.log_viewer import LogViewerModule
from modules.backup import BackupModule
from modules.service_manager import ServiceManagerModule
from modules.server_transfer import ServerTransferModule
from modules.server_backup import ServerBackupModule
from modules.firewall_manager import FirewallManagerModule
from modules.k8s_manager import K8sManagerModule


class SentinelAI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 SSH Manager Pro")
        self.root.geometry("1400x850")
        self.root.minsize(1200, 700)
        
        # Core bileşenler
        self.ssh = SSHClientManager()
        self.key_manager = KeyManager()
        
        # Veri yükleme
        self.config_file = Path.home() / ".ssh_manager_servers.json"
        self.servers = self.load_servers()
        
        # Anahtar kontrolü
        self.key_manager.ensure_key_exists()
        
        # Ana container - PanedWindow ile bölünmüş ekran
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sol panel (sunucu listesi)
        left_frame = self.setup_server_panel()
        main_paned.add(left_frame, weight=1)
        
        # Sağ panel (notebook)
        right_frame = self.setup_modules()
        main_paned.add(right_frame, weight=5)
        
        # Durum çubuğu
        self.status_bar = tk.Label(root, text="✅ Hazır - Sunucu ekleyip bağlanabilirsiniz", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Sunucu listesini modüllere gönder
        self.update_modules_server_list()
    
    def setup_server_panel(self):
        """Sol panel: Sunucu listesi ve ekleme/silme"""
        left_frame = tk.Frame(self.root, width=280)
        left_frame.pack_propagate(False)
        
        # Başlık
        tk.Label(left_frame, text="📡 SUNUCULAR", font=("Arial", 11, "bold"), fg="#2196F3").pack(anchor=tk.W, pady=5, padx=5)
        
        # Sunucu listesi
        self.server_listbox = tk.Listbox(left_frame, height=15, font=("Consolas", 9), selectbackground="#2196F3")
        self.server_listbox.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        self.server_listbox.bind("<<ListboxSelect>>", self.on_server_select)
        
        # Butonlar
        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Button(btn_frame, text="➕ Ekle", command=self.add_server, 
                 bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="✏️ Düzenle", command=self.edit_server, 
                 bg="#FF9800", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="🗑️ Sil", command=self.delete_server, 
                 bg="#f44336", fg="white", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        # Bilgi
        info_label = tk.Label(left_frame, text="💡 İpucu: Sunucuya çift tıklayarak\nTerminal sekmesinde bağlanabilirsiniz", 
                              font=("Arial", 8), fg="gray", justify=tk.LEFT)
        info_label.pack(pady=10, padx=5)
        
        self.refresh_server_list()
        return left_frame
    
    def setup_modules(self):
        """Sağ panel: Sekmeli modüller"""
        self.notebook = ttk.Notebook(self.root)
        
        # Tüm modülleri oluştur
        self.terminal_module = TerminalModule(self.notebook, self.ssh, self.key_manager)
        self.file_browser = FileBrowserModule(self.notebook, self.ssh)
        self.file_transfer = FileTransferModule(self.notebook, self.ssh)
        self.bulk_commands = BulkCommandsModule(self.notebook, self.ssh, self.key_manager)
        self.monitoring = MonitoringModule(self.notebook, self.ssh)
        self.log_viewer = LogViewerModule(self.notebook, self.ssh)
        self.backup = BackupModule(self.notebook, self.ssh)
        self.service_manager = ServiceManagerModule(self.notebook, self.ssh)
        self.server_transfer = ServerTransferModule(self.notebook, self.ssh, self.key_manager)
        self.server_backup = ServerBackupModule(self.notebook, self.ssh, self.key_manager)
        self.firewall_manager = FirewallManagerModule(self.notebook, self.ssh)  # YENİ
        self.k8s_manager = K8sManagerModule(self.notebook, self.ssh)            # YENİ
        
        # Sekmelere ekle (düzenli sıralama)
        self.notebook.add(self.terminal_module.get_frame(), text="🖥️ Terminal")
        self.notebook.add(self.file_browser.get_frame(), text="📁 Dosya Gezgini")
        self.notebook.add(self.file_transfer.get_frame(), text="📤 PC ↔ Sunucu")
        self.notebook.add(self.server_transfer.get_frame(), text="🔄 Sunucu → Sunucu")
        self.notebook.add(self.server_backup.get_frame(), text="💾 Sunucu Backup")
        self.notebook.add(self.bulk_commands.get_frame(), text="⚡ Toplu Komut")
        self.notebook.add(self.monitoring.get_frame(), text="📊 İzleme")
        self.notebook.add(self.log_viewer.get_frame(), text="📜 Log İzleyici")
        self.notebook.add(self.backup.get_frame(), text="💻 PC Backup")
        self.notebook.add(self.service_manager.get_frame(), text="🛠️ Servisler")
        self.notebook.add(self.firewall_manager.get_frame(), text="🔥 Firewall")      # YENİ
        self.notebook.add(self.k8s_manager.get_frame(), text="☸️ Kubernetes")         # YENİ
        
        return self.notebook
    
    def load_servers(self):
        """Kayıtlı sunucuları JSON'dan yükle"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_servers(self):
        """Sunucuları JSON'a kaydet"""
        with open(self.config_file, 'w') as f:
            json.dump(self.servers, f, indent=2)
    
    def refresh_server_list(self):
        """Sol paneldeki sunucu listesini yenile"""
        self.server_listbox.delete(0, tk.END)
        for server in self.servers:
            status = "🔌" if self.ssh.is_connected(server['name']) else "⚪"
            self.server_listbox.insert(tk.END, f"{status} {server['name']} ({server['ip']})")
    
    def update_modules_server_list(self):
        """Tüm modüllerin sunucu listesini güncelle"""
        if hasattr(self, 'terminal_module'):
            self.terminal_module.update_server_list(self.servers)
        if hasattr(self, 'file_browser'):
            self.file_browser.update_server_list(self.servers)
        if hasattr(self, 'file_transfer'):
            self.file_transfer.update_server_list(self.servers)
        if hasattr(self, 'bulk_commands'):
            self.bulk_commands.update_server_list(self.servers)
        if hasattr(self, 'monitoring'):
            self.monitoring.update_server_list(self.servers)
        if hasattr(self, 'log_viewer'):
            self.log_viewer.update_server_list(self.servers)
        if hasattr(self, 'backup'):
            self.backup.update_server_list(self.servers)
        if hasattr(self, 'service_manager'):
            self.service_manager.update_server_list(self.servers)
        if hasattr(self, 'server_transfer'):
            self.server_transfer.update_server_list(self.servers)
        if hasattr(self, 'server_backup'):
            self.server_backup.update_server_list(self.servers)
        if hasattr(self, 'firewall_manager'):
            self.firewall_manager.update_server_list(self.servers)
        if hasattr(self, 'k8s_manager'):
            self.k8s_manager.update_server_list(self.servers)
    
    def on_server_select(self, event):
        """Listeden sunucu seçildiğinde çalışır"""
        selection = self.server_listbox.curselection()
        if not selection:
            self.selected_server = None
            return
        
        selected_text = self.server_listbox.get(selection[0])
        # İkonu atla (2 karakter)
        without_icon = selected_text[2:] if selected_text[0] in ['🔌', '⚪'] else selected_text
        server_name = without_icon.split("(")[0].strip()
        self.selected_server = next((s for s in self.servers if s["name"] == server_name), None)
        
        if self.selected_server:
            self.status_bar.config(text=f"✅ Seçili: {self.selected_server['name']} ({self.selected_server['ip']})")
    
    def add_server(self):
        """Yeni sunucu ekleme dialog'u"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Yeni Sunucu Ekle")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Ortala
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        fields = {}
        labels = [
            ("Sunucu Adı*:", "name"),
            ("IP Adresi*:", "ip"),
            ("Kullanıcı*:", "user", "root"),
            ("Port:", "port", "22"),
            ("Grup:", "group", "Default"),
            ("Açıklama:", "description", "")
        ]
        
        row = 0
        for label in labels:
            tk.Label(dialog, text=label[0], font=("Arial", 9, "bold")).grid(row=row, column=0, sticky=tk.W, padx=10, pady=5)
            entry = tk.Entry(dialog, width=30, font=("Arial", 9))
            if len(label) > 2:
                entry.insert(0, label[2])
            entry.grid(row=row, column=1, padx=10, pady=5)
            fields[label[1]] = entry
            row += 1
        
        def save():
            if not fields["name"].get() or not fields["ip"].get():
                messagebox.showerror("Hata", "Sunucu adı ve IP adresi zorunludur!")
                return
            
            # Aynı isimde sunucu var mı kontrol et
            if any(s['name'] == fields["name"].get() for s in self.servers):
                messagebox.showerror("Hata", "Bu sunucu adı zaten mevcut!")
                return
            
            server = {
                "name": fields["name"].get(),
                "ip": fields["ip"].get(),
                "user": fields["user"].get(),
                "port": int(fields["port"].get()) if fields["port"].get().isdigit() else 22,
                "group": fields["group"].get(),
                "description": fields["description"].get(),
                "key_uploaded": False
            }
            self.servers.append(server)
            self.save_servers()
            self.refresh_server_list()
            self.update_modules_server_list()
            dialog.destroy()
            
            # Anahtar yükleme teklifi
            if messagebox.askyesno("Anahtar Yükleme", 
                                   f"✅ {server['name']} sunucusu eklendi!\n\n"
                                   f"Şimdi SSH anahtarını bu sunucuya otomatik yüklemek ister misiniz?\n"
                                   f"(Sadece bir kere şifre girmeniz yeterli, sonrasında şifresiz bağlanabilirsiniz)"):
                password = simpledialog.askstring("SSH Şifresi", 
                                                  f"{server['user']}@{server['ip']}\n\nSunucu şifresini girin:", 
                                                  show='*')
                if password:
                    try:
                        self.key_manager.upload_to_server(server, password)
                        server['key_uploaded'] = True
                        self.save_servers()
                        self.refresh_server_list()
                        messagebox.showinfo("Başarılı", "✅ SSH anahtarı başarıyla yüklendi!\nArtık şifresiz bağlanabilirsiniz.")
                        self.status_bar.config(text=f"✅ {server['name']} - Anahtar yüklendi")
                    except Exception as e:
                        messagebox.showerror("Hata", f"Anahtar yüklenemedi:\n{str(e)}\n\nDaha sonra 'Anahtar Yükle' butonunu kullanabilirsiniz.")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        tk.Button(btn_frame, text="💾 Kaydet", command=save, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold"), padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="İptal", command=dialog.destroy, 
                 bg="#9E9E9E", fg="white", font=("Arial", 10), padx=20).pack(side=tk.LEFT)
    
    def edit_server(self):
        """Seçili sunucuyu düzenle (sil-yeniden ekle yöntemi)"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            messagebox.showwarning("Uyarı", "Lütfen önce düzenlenecek sunucuyu seçin!")
            return
        
        if messagebox.askyesno("Düzenle", 
                               f"'{self.selected_server['name']}' sunucusunu düzenlemek için\n"
                               f"önce silip sonra tekrar eklemelisiniz.\n\n"
                               f"Devam etmek istiyor musunuz?"):
            name = self.selected_server['name']
            self.servers.remove(self.selected_server)
            self.save_servers()
            self.refresh_server_list()
            self.update_modules_server_list()
            self.selected_server = None
            self.add_server()
            self.status_bar.config(text=f"✏️ {name} düzenleniyor - Yeni bilgileri girin")
    
    def delete_server(self):
        """Seçili sunucuyu sil"""
        if not hasattr(self, 'selected_server') or not self.selected_server:
            messagebox.showwarning("Uyarı", "Lütfen önce silinecek sunucuyu seçin!")
            return
        
        if messagebox.askyesno("Onay", 
                               f"⚠️ '{self.selected_server['name']}' sunucusu silinecek!\n\n"
                               f"Bu işlem geri alınamaz. Devam etmek istiyor musunuz?"):
            name = self.selected_server['name']
            # Bağlantıyı kapat
            if self.ssh.is_connected(name):
                self.ssh.disconnect(name)
            self.servers.remove(self.selected_server)
            self.save_servers()
            self.refresh_server_list()
            self.update_modules_server_list()
            self.selected_server = None
            self.status_bar.config(text=f"🗑️ {name} silindi")
    
    def on_closing(self):
        """Uygulama kapanırken bağlantıları temizle"""
        for server in self.servers:
            if self.ssh.is_connected(server['name']):
                self.ssh.disconnect(server['name'])
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    
    # Uygulama ikonu (opsiyonel)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = SentinelAI(root)
    
    # Kapanış işlemi
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    root.mainloop()