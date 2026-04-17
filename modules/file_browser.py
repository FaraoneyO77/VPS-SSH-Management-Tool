import tkinter as tk
from tkinter import ttk, messagebox
import threading
from stat import S_ISDIR

class FileBrowserModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.current_server = None
        self.current_path = "/root"
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        # Üst çubuk
        top_frame = tk.Frame(self.frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(top_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(top_frame, state="readonly", width=30)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        self.server_combo.bind("<<ComboboxSelected>>", lambda e: self.load_browser())
        
        self.refresh_btn = tk.Button(top_frame, text="🔄 Yenile", command=self.load_browser)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Üst klasör butonu (YENİ!)
        self.parent_btn = tk.Button(top_frame, text="📁 .. (Üst Klasör)", command=self.go_parent,
                                     bg="#FF9800", fg="white")
        self.parent_btn.pack(side=tk.LEFT, padx=5)
        
        # Yol göstergesi
        self.path_label = tk.Label(self.frame, text="Yol: /", font=("Arial", 9), fg="blue", anchor=tk.W)
        self.path_label.pack(fill=tk.X, pady=5)
        
        # Dosya ağacı
        self.tree = ttk.Treeview(self.frame, columns=("type", "size"), show="tree headings", height=25)
        self.tree.heading("#0", text="Ad")
        self.tree.heading("type", text="Tip")
        self.tree.heading("size", text="Boyut")
        self.tree.column("type", width=80)
        self.tree.column("size", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        
        # Sağ tık menüsü
        self.context_menu = tk.Menu(self.frame, tearoff=0)
        self.context_menu.add_command(label="📥 İndir (PC'ye)", command=self.download_file)
        self.context_menu.add_command(label="📤 Yükle (PC'den)", command=self.upload_file)
        self.tree.bind("<Button-3>", self.show_context_menu)
        
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
    
    def load_browser(self):
        server = self.get_selected_server()
        if not server:
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna terminal ile bağlanın!")
            return
        
        self.current_server = server
        self.load_directory(self.current_path)
    
    def go_parent(self):
        """Üst klasöre çık"""
        if self.current_path == "/":
            return
        # Son '/'den önceki kısmı al
        parent = "/".join(self.current_path.rstrip('/').split('/')[:-1])
        if not parent:
            parent = "/"
        self.current_path = parent
        self.load_directory(parent)
    
    def load_directory(self, path):
        if not self.current_server:
            return
        
        self.status_label.config(text=f"Yükleniyor: {path}...", fg="orange")
        self.path_label.config(text=f"Yol: {path}")
        
        def load():
            try:
                sftp = self.ssh.get_sftp(self.current_server['name'])
                items = sftp.listdir_attr(path)
                
                self.parent.after(0, lambda: self.tree.delete(*self.tree.get_children()))
                
                # Üst klasör (..) ekle - sadece root değilse
                if path != "/":
                    self.parent.after(0, lambda: self.tree.insert("", "end", text="📁 ..", values=("parent", "")))
                
                for item in sorted(items, key=lambda x: x.filename):
                    name = item.filename
                    if name in ['.', '..']:
                        continue
                    
                    is_dir = S_ISDIR(item.st_mode)
                    icon = "📁" if is_dir else "📄"
                    size = self.format_size(item.st_size) if not is_dir else "-"
                    item_type = "dir" if is_dir else "file"
                    
                    self.parent.after(0, lambda n=name, i=icon, t=item_type, s=size: 
                                      self.tree.insert("", "end", text=f"{i} {n}", values=(t, s)))
                
                sftp.close()
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ {len(items)} öğe yüklendi", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(text=f"❌ Hata: {str(e)}", fg="red"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        text = item['text']
        item_type = item['values'][0] if item['values'] else None
        
        # Üst klasör kontrolü
        if ".." in text:
            self.go_parent()
            return
        
        name = text.split(" ", 1)[1] if " " in text else text
        
        if item_type == "dir":
            new_path = f"{self.current_path}/{name}".replace("//", "/")
            self.current_path = new_path
            self.load_directory(new_path)
    
    def show_context_menu(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item = self.tree.item(selected[0])
        item_type = item['values'][0] if item['values'] else None
        if item_type == "file":
            self.context_menu.post(event.x_root, event.y_root)
    
    def download_file(self):
        selected = self.tree.selection()
        if not selected:
            return
        
        item = self.tree.item(selected[0])
        text = item['text']
        name = text.split(" ", 1)[1] if " " in text else text
        
        from tkinter import filedialog
        save_path = filedialog.asksaveasfilename(initialfile=name, title="Dosyayı Kaydet")
        if not save_path:
            return
        
        remote_path = f"{self.current_path}/{name}".replace("//", "/")
        client = self.ssh.active_connections.get(self.current_server['name'])
        
        def download():
            try:
                sftp = client.open_sftp()
                sftp.get(remote_path, save_path)
                sftp.close()
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", f"Dosya indirildi:\n{save_path}"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"İndirme hatası:\n{str(e)}"))
        
        threading.Thread(target=download, daemon=True).start()
    
    def upload_file(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(title="Yüklenecek Dosyayı Seç")
        if not file_path:
            return
        
        from pathlib import Path
        file_name = Path(file_path).name
        remote_path = f"{self.current_path}/{file_name}".replace("//", "/")
        client = self.ssh.active_connections.get(self.current_server['name'])
        
        def upload():
            try:
                sftp = client.open_sftp()
                sftp.put(file_path, remote_path)
                sftp.close()
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", f"Dosya yüklendi:\n{remote_path}"))
                self.parent.after(0, self.load_browser)
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"Yükleme hatası:\n{str(e)}"))
        
        threading.Thread(target=upload, daemon=True).start()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_frame(self):
        return self.frame