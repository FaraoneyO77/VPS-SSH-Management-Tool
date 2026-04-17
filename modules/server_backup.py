import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import paramiko
import datetime
from pathlib import Path

class ServerBackupModule:
    def __init__(self, parent, ssh_manager, key_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.key_manager = key_manager
        self.servers = []
        self.backup_jobs = []
        self.config_file = Path.home() / ".server_backup_config.json"
        
        self.load_jobs()
        self.setup_ui()
    
    def load_jobs(self):
        if self.config_file.exists():
            import json
            with open(self.config_file, 'r') as f:
                self.backup_jobs = json.load(f)
    
    def save_jobs(self):
        import json
        with open(self.config_file, 'w') as f:
            json.dump(self.backup_jobs, f, indent=2)
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        tk.Label(self.frame, text="💾 SUNUCUDAN SUNUCUYA BACKUP", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(self.frame, text="Bir sunucudaki dosyaları diğer sunucuya yedekler", font=("Arial", 9), fg="gray").pack()
        
        # Backup görevleri
        tasks_frame = tk.LabelFrame(self.frame, text="Backup Görevleri", padx=5, pady=5)
        tasks_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        columns = ("Kaynak", "Hedef", "Kaynak Klasör", "Hedef Klasör", "Zamanlama", "Durum")
        self.tasks_tree = ttk.Treeview(tasks_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=120)
        self.tasks_tree.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(tasks_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="➕ Yeni Görev", command=self.add_backup_task).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Sil", command=self.delete_backup_task).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="▶ Şimdi Çalıştır", command=self.run_backup_now).pack(side=tk.LEFT, padx=2)
        
        # Manuel Backup
        manual_frame = tk.LabelFrame(self.frame, text="Manuel Backup (Sunucu → Sunucu)", padx=10, pady=10)
        manual_frame.pack(fill=tk.X, pady=5, padx=5)
        
        row = 0
        tk.Label(manual_frame, text="Kaynak Sunucu:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.source_combo = ttk.Combobox(manual_frame, state="readonly", width=30)
        self.source_combo.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        tk.Label(manual_frame, text="Kaynak Klasör:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.source_entry = tk.Entry(manual_frame, width=40)
        self.source_entry.insert(0, "/etc")
        self.source_entry.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        tk.Label(manual_frame, text="Hedef Sunucu:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.target_combo = ttk.Combobox(manual_frame, state="readonly", width=30)
        self.target_combo.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        tk.Label(manual_frame, text="Hedef Klasör:").grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
        self.target_entry = tk.Entry(manual_frame, width=40)
        self.target_entry.insert(0, "/backup")
        self.target_entry.grid(row=row, column=1, padx=5, pady=2)
        row += 1
        
        tk.Button(manual_frame, text="📦 Hemen Yedekle", command=self.manual_backup,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).grid(row=row, column=0, columnspan=2, pady=10)
        
        # İlerleme
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5, padx=5)
        
        # Sonuç
        self.result_text = tk.Text(self.frame, height=8, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Durum
        self.status_label = tk.Label(self.frame, text="Hazır", font=("Arial", 8), fg="gray")
        self.status_label.pack()
        
        self.refresh_task_list()
    
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
    
    def add_backup_task(self):
        dialog = tk.Toplevel(self.frame)
        dialog.title("Backup Görevi Ekle")
        dialog.geometry("450x400")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        fields = {}
        row = 0
        
        tk.Label(dialog, text="Kaynak Sunucu:").grid(row=row, column=0, padx=5, pady=5)
        source_combo = ttk.Combobox(dialog, state="readonly", width=30)
        source_combo['values'] = [f"{s['name']} ({s['ip']})" for s in self.servers]
        source_combo.grid(row=row, column=1, padx=5)
        fields['source'] = source_combo
        row += 1
        
        tk.Label(dialog, text="Kaynak Klasör:").grid(row=row, column=0, padx=5, pady=5)
        source_entry = tk.Entry(dialog, width=30)
        source_entry.insert(0, "/etc")
        source_entry.grid(row=row, column=1, padx=5)
        fields['source_path'] = source_entry
        row += 1
        
        tk.Label(dialog, text="Hedef Sunucu:").grid(row=row, column=0, padx=5, pady=5)
        target_combo = ttk.Combobox(dialog, state="readonly", width=30)
        target_combo['values'] = [f"{s['name']} ({s['ip']})" for s in self.servers]
        target_combo.grid(row=row, column=1, padx=5)
        fields['target'] = target_combo
        row += 1
        
        tk.Label(dialog, text="Hedef Klasör:").grid(row=row, column=0, padx=5, pady=5)
        target_entry = tk.Entry(dialog, width=30)
        target_entry.insert(0, "/backup")
        target_entry.grid(row=row, column=1, padx=5)
        fields['target_path'] = target_entry
        row += 1
        
        tk.Label(dialog, text="Zamanlama (saat):").grid(row=row, column=0, padx=5, pady=5)
        hour_spin = tk.Spinbox(dialog, from_=0, to=23, width=5)
        hour_spin.delete(0, tk.END)
        hour_spin.insert(0, "3")
        hour_spin.grid(row=row, column=1, sticky=tk.W, padx=5)
        fields['hour'] = hour_spin
        row += 1
        
        def save():
            source_text = source_combo.get()
            target_text = target_combo.get()
            if not source_text or not target_text:
                messagebox.showerror("Hata", "Kaynak ve hedef sunucu seçin!")
                return
            
            job = {
                "source": source_text.split(" ")[0],
                "source_path": source_entry.get(),
                "target": target_text.split(" ")[0],
                "target_path": target_entry.get(),
                "hour": int(hour_spin.get()),
                "enabled": True
            }
            self.backup_jobs.append(job)
            self.save_jobs()
            self.refresh_task_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Kaydet", command=save, bg="#4CAF50", fg="white").grid(row=row, column=0, columnspan=2, pady=20)
    
    def delete_backup_task(self):
        selected = self.tasks_tree.selection()
        if not selected:
            return
        index = int(selected[0].split('I')[1]) - 1 if 'I' in selected[0] else 0
        if index < len(self.backup_jobs):
            del self.backup_jobs[index]
            self.save_jobs()
            self.refresh_task_list()
    
    def refresh_task_list(self):
        self.tasks_tree.delete(*self.tasks_tree.get_children())
        for job in self.backup_jobs:
            status = "✅ Aktif" if job.get('enabled', True) else "⏸ Pasif"
            self.tasks_tree.insert("", tk.END, values=(
                job['source'],
                job['target'],
                job['source_path'],
                job['target_path'],
                f"{job['hour']}:00",
                status
            ))
    
    def run_backup_now(self):
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir backup görevi seçin!")
            return
        
        index = int(selected[0].split('I')[1]) - 1 if 'I' in selected[0] else 0
        if index < len(self.backup_jobs):
            job = self.backup_jobs[index]
            self.do_backup(job['source'], job['source_path'], job['target'], job['target_path'])
    
    def manual_backup(self):
        source_server = self.get_server_from_combo(self.source_combo)
        target_server = self.get_server_from_combo(self.target_combo)
        
        if not source_server or not target_server:
            messagebox.showwarning("Uyarı", "Lütfen kaynak ve hedef sunucuyu seçin!")
            return
        
        source_path = self.source_entry.get()
        target_path = self.target_entry.get()
        
        self.do_backup(source_server['name'], source_path, target_server['name'], target_path)
    
    def do_backup(self, source_name, source_path, target_name, target_path):
        source_server = next((s for s in self.servers if s['name'] == source_name), None)
        target_server = next((s for s in self.servers if s['name'] == target_name), None)
        
        if not source_server or not target_server:
            self.result_text.insert(tk.END, "❌ Sunucu bulunamadı!\n")
            return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_name}_{Path(source_path).name}_{timestamp}.tar.gz"
        remote_backup_path = f"{target_path}/{backup_name}".replace("//", "/")
        
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"🔄 Backup başlıyor:\n")
        self.result_text.insert(tk.END, f"   Kaynak: {source_name}:{source_path}\n")
        self.result_text.insert(tk.END, f"   Hedef: {target_name}:{remote_backup_path}\n")
        self.result_text.see(tk.END)
        
        self.progress_var.set(0)
        self.status_label.config(text="Backup yapılıyor...", fg="orange")
        
        def backup_thread():
            try:
                # Kaynak bağlantı
                if self.ssh.is_connected(source_name):
                    source_client = self.ssh.active_connections.get(source_name)
                else:
                    source_client = self.connect_to_server(source_server)
                    close_source = True
                
                # Hedef bağlantı
                if self.ssh.is_connected(target_name):
                    target_client = self.ssh.active_connections.get(target_name)
                else:
                    target_client = self.connect_to_server(target_server)
                    close_target = True
                
                # Kaynakta tar ve sıkıştır
                tar_cmd = f"tar -czf - {source_path} 2>/dev/null"
                stdin, stdout, stderr = source_client.exec_command(tar_cmd)
                
                # Hedefte yaz
                target_sftp = target_client.open_sftp()
                with target_sftp.open(remote_backup_path, 'wb') as f:
                    data = stdout.read(1024 * 1024)
                    total = 0
                    while data:
                        f.write(data)
                        total += len(data)
                        data = stdout.read(1024 * 1024)
                
                target_sftp.close()
                
                if close_source:
                    source_client.close()
                if close_target:
                    target_client.close()
                
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"✅ Backup başarılı!\n"))
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"   Dosya: {remote_backup_path}\n"))
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"   Boyut: {self.format_size(total)}\n"))
                self.parent.after(0, lambda: self.status_label.config(text="✅ Backup tamamlandı", fg="green"))
                self.parent.after(0, lambda: self.progress_var.set(100))
                
            except Exception as e:
                self.parent.after(0, lambda: self.result_text.insert(tk.END, f"❌ Backup hatası: {str(e)}\n"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ Backup hatası", fg="red"))
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def get_frame(self):
        return self.frame