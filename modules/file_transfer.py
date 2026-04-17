import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from pathlib import Path

class FileTransferModule:
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
        self.server_combo.bind("<<ComboboxSelected>>", lambda e: self.load_transfer())
        
        # Transfer butonları
        btn_frame = tk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.upload_btn = tk.Button(btn_frame, text="📤 Dosya Yükle (PC → Sunucu)", 
                                     command=self.upload_file, bg="#2196F3", fg="white",
                                     font=("Arial", 10), padx=20, pady=5)
        self.upload_btn.pack(side=tk.LEFT, padx=10)
        
        self.download_btn = tk.Button(btn_frame, text="📥 Dosya İndir (Sunucu → PC)", 
                                       command=self.download_file, bg="#FF9800", fg="white",
                                       font=("Arial", 10), padx=20, pady=5)
        self.download_btn.pack(side=tk.LEFT, padx=10)
        
        # Dosya listesi
        list_frame = tk.Frame(self.frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(list_frame, text="Sunucudaki Dosyalar (çift tıkla indir):", font=("Arial", 9, "bold")).pack(anchor=tk.W)
        
        self.file_listbox = tk.Listbox(list_frame, height=15, font=("Consolas", 9))
        self.file_listbox.pack(fill=tk.BOTH, expand=True)
        self.file_listbox.bind("<Double-1>", lambda e: self.download_file())
        
        # İlerleme çubuğu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
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
    
    def load_transfer(self):
        server = self.get_selected_server()
        if not server:
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna terminal ile bağlanın!")
            return
        
        self.current_server = server
        self.list_files("/root")
    
    def list_files(self, path):
        self.file_listbox.delete(0, tk.END)
        self.file_listbox.insert(tk.END, "📁 .. (üst dizin)")
        
        def load():
            try:
                sftp = self.ssh.get_sftp(self.current_server['name'])
                items = sftp.listdir_attr(path)
                
                for item in sorted(items, key=lambda x: x.filename):
                    name = item.filename
                    from stat import S_ISDIR
                    if S_ISDIR(item.st_mode):
                        self.parent.after(0, lambda n=name: self.file_listbox.insert(tk.END, f"📁 {n}/"))
                    else:
                        size = self.format_size(item.st_size)
                        self.parent.after(0, lambda n=name, s=size: self.file_listbox.insert(tk.END, f"📄 {n} ({s})"))
                
                sftp.close()
                self.current_path = path
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ {len(items)} dosya listelendi", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(text=f"❌ Hata: {str(e)}", fg="red"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def upload_file(self):
        if not self.current_server:
            messagebox.showwarning("Uyarı", "Önce bir sunucu seçin!")
            return
        
        file_path = filedialog.askopenfilename(title="Yüklenecek Dosyayı Seç")
        if not file_path:
            return
        
        file_name = Path(file_path).name
        remote_path = f"{self.current_path}/{file_name}".replace("//", "/")
        
        if not messagebox.askyesno("Onay", f"Dosya yüklenecek:\n{file_path}\n→ {remote_path}"):
            return
        
        self.progress_var.set(0)
        self.status_label.config(text=f"Yükleniyor: {file_name}...", fg="orange")
        
        def upload():
            try:
                sftp = self.ssh.get_sftp(self.current_server['name'])
                sftp.put(file_path, remote_path, callback=self.update_progress)
                sftp.close()
                
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", f"Dosya yüklendi:\n{remote_path}"))
                self.parent.after(0, lambda: self.list_files(self.current_path))
                self.parent.after(0, lambda: self.status_label.config(text="✅ Yükleme tamamlandı", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"Yükleme hatası:\n{str(e)}"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ Yükleme hatası", fg="red"))
            finally:
                self.parent.after(0, lambda: self.progress_var.set(0))
        
        threading.Thread(target=upload, daemon=True).start()
    
    def download_file(self):
        if not self.current_server:
            messagebox.showwarning("Uyarı", "Önce bir sunucu seçin!")
            return
        
        selected = self.file_listbox.curselection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen indirilecek dosyayı seçin!")
            return
        
        selected_text = self.file_listbox.get(selected[0])
        if "📁" in selected_text:
            # Klasör seçildi, içine gir
            dir_name = selected_text.split(" ")[1].rstrip("/")
            new_path = f"{self.current_path}/{dir_name}".replace("//", "/")
            self.list_files(new_path)
            return
        elif "📄" in selected_text:
            # Dosya seçildi
            file_info = selected_text.split(" ")[1]
            file_name = file_info.split(" (")[0]
        else:
            # ".." seçildi
            if ".." in selected_text:
                parent = "/".join(self.current_path.split("/")[:-1]) or "/"
                self.list_files(parent)
            return
        
        remote_path = f"{self.current_path}/{file_name}".replace("//", "/")
        save_path = filedialog.asksaveasfilename(initialfile=file_name, title="Dosyayı Kaydet")
        
        if not save_path:
            return
        
        self.progress_var.set(0)
        self.status_label.config(text=f"İndiriliyor: {file_name}...", fg="orange")
        
        def download():
            try:
                sftp = self.ssh.get_sftp(self.current_server['name'])
                sftp.get(remote_path, save_path, callback=self.update_progress)
                sftp.close()
                
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", f"Dosya indirildi:\n{save_path}"))
                self.parent.after(0, lambda: self.status_label.config(text="✅ İndirme tamamlandı", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"İndirme hatası:\n{str(e)}"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ İndirme hatası", fg="red"))
            finally:
                self.parent.after(0, lambda: self.progress_var.set(0))
        
        threading.Thread(target=download, daemon=True).start()
    
    def update_progress(self, transferred, total):
        percent = (transferred / total) * 100
        self.parent.after(0, lambda: self.progress_var.set(percent))
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def get_frame(self):
        return self.frame