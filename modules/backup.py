import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from pathlib import Path
import datetime

class BackupModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.servers = []
        self.config_file = Path.home() / ".backup_config.json"
        self.backup_configs = self.load_configs()
        
        self.setup_ui()
    
    def load_configs(self):
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_configs(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.backup_configs, f, indent=2)
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        tk.Label(self.frame, text="💾 OTOMATİK BACKUP", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Backup görevleri listesi
        list_frame = tk.LabelFrame(self.frame, text="Backup Görevleri", padx=5, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        columns = ("Sunucu", "Kaynak", "Hedef", "Zamanlama", "Durum")
        self.task_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)
        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=100)
        self.task_tree.pack(fill=tk.BOTH, expand=True)
        
        # Butonlar
        btn_frame = tk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="➕ Yeni Görev", command=self.add_task).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Sil", command=self.delete_task).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="▶ Şimdi Çalıştır", command=self.run_backup).pack(side=tk.LEFT, padx=2)
        
        # Manuel backup
        manual_frame = tk.LabelFrame(self.frame, text="Manuel Backup", padx=5, pady=5)
        manual_frame.pack(fill=tk.X, pady=5, padx=5)
        
        row = 0
        tk.Label(manual_frame, text="Sunucu:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.server_combo = ttk.Combobox(manual_frame, state="readonly", width=30)
        self.server_combo.grid(row=row, column=1, padx=5)
        row += 1
        
        tk.Label(manual_frame, text="Kaynak Klasör:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.source_entry = tk.Entry(manual_frame, width=40)
        self.source_entry.insert(0, "/etc")
        self.source_entry.grid(row=row, column=1, padx=5)
        row += 1
        
        tk.Label(manual_frame, text="Yerel Hedef:").grid(row=row, column=0, sticky=tk.W, padx=5)
        self.target_entry = tk.Entry(manual_frame, width=40)
        self.target_entry.insert(0, str(Path.home() / "backups"))
        self.target_entry.grid(row=row, column=1, padx=5)
        row += 1
        
        tk.Button(manual_frame, text="📦 Hemen Yedekle", command=self.manual_backup, bg="#2196F3", fg="white").grid(row=row, column=0, columnspan=2, pady=10)
        
        # İlerleme
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5, padx=5)
        
        self.status_label = tk.Label(self.frame, text="Hazır", font=("Arial", 8), fg="gray")
        self.status_label.pack()
        
        self.refresh_task_list()
    
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
    
    def add_task(self):
        dialog = tk.Toplevel(self.frame)
        dialog.title("Backup Görevi Ekle")
        dialog.geometry("400x300")
        dialog.transient(self.frame)
        dialog.grab_set()
        
        fields = {}
        row = 0
        
        tk.Label(dialog, text="Sunucu:").grid(row=row, column=0, padx=5, pady=5)
        server_combo = ttk.Combobox(dialog, state="readonly", width=30)
        server_combo['values'] = [f"{s['name']} ({s['ip']})" for s in self.servers]
        server_combo.grid(row=row, column=1, padx=5)
        fields['server'] = server_combo
        row += 1
        
        tk.Label(dialog, text="Kaynak Klasör:").grid(row=row, column=0, padx=5, pady=5)
        source_entry = tk.Entry(dialog, width=30)
        source_entry.insert(0, "/etc")
        source_entry.grid(row=row, column=1, padx=5)
        fields['source'] = source_entry
        row += 1
        
        tk.Label(dialog, text="Yerel Hedef:").grid(row=row, column=0, padx=5, pady=5)
        target_entry = tk.Entry(dialog, width=30)
        target_entry.insert(0, str(Path.home() / "backups"))
        target_entry.grid(row=row, column=1, padx=5)
        fields['target'] = target_entry
        row += 1
        
        tk.Label(dialog, text="Zamanlama (saat):").grid(row=row, column=0, padx=5, pady=5)
        hour_spin = tk.Spinbox(dialog, from_=0, to=23, width=5)
        hour_spin.delete(0, tk.END)
        hour_spin.insert(0, "3")
        hour_spin.grid(row=row, column=1, sticky=tk.W, padx=5)
        fields['hour'] = hour_spin
        row += 1
        
        def save():
            server_text = server_combo.get()
            if not server_text:
                messagebox.showerror("Hata", "Sunucu seçin!")
                return
            
            server_name = server_text.split(" ")[0]
            task = {
                "server": server_name,
                "source": source_entry.get(),
                "target": target_entry.get(),
                "hour": int(hour_spin.get()),
                "enabled": True
            }
            self.backup_configs.append(task)
            self.save_configs()
            self.refresh_task_list()
            dialog.destroy()
        
        tk.Button(dialog, text="Kaydet", command=save, bg="#4CAF50", fg="white").grid(row=row, column=0, columnspan=2, pady=20)
    
    def delete_task(self):
        selected = self.task_tree.selection()
        if not selected:
            return
        index = int(selected[0].split('I')[1]) - 1 if 'I' in selected[0] else 0
        if index < len(self.backup_configs):
            del self.backup_configs[index]
            self.save_configs()
            self.refresh_task_list()
    
    def refresh_task_list(self):
        self.task_tree.delete(*self.task_tree.get_children())
        for task in self.backup_configs:
            status = "✅ Aktif" if task.get('enabled', True) else "⏸ Pasif"
            self.task_tree.insert("", tk.END, values=(
                task['server'],
                task['source'],
                task['target'],
                f"{task['hour']}:00",
                status
            ))
    
    def run_backup(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir backup görevi seçin!")
            return
        
        index = int(selected[0].split('I')[1]) - 1 if 'I' in selected[0] else 0
        if index < len(self.backup_configs):
            task = self.backup_configs[index]
            self.do_backup(task['server'], task['source'], task['target'])
    
    def manual_backup(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        source = self.source_entry.get()
        target = self.target_entry.get()
        
        if not source or not target:
            messagebox.showwarning("Uyarı", "Kaynak ve hedef belirtin!")
            return
        
        self.do_backup(server['name'], source, target)
    
    def do_backup(self, server_name, source, target):
        if not self.ssh.is_connected(server_name):
            messagebox.showwarning("Uyarı", f"Önce {server_name} sunucusuna bağlanın!")
            return
        
        Path(target).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{server_name}_{Path(source).name}_{timestamp}.tar.gz"
        local_path = Path(target) / backup_name
        
        self.status_label.config(text=f"Yedekleniyor: {server_name}...", fg="orange")
        self.progress_var.set(0)
        
        def backup_thread():
            client = self.ssh.active_connections.get(server_name)
            try:
                # Tar ve sıkıştır
                tar_cmd = f"tar -czf - {source} 2>/dev/null"
                stdin, stdout, stderr = client.exec_command(tar_cmd)
                
                # Yerel dosyaya yaz
                with open(local_path, 'wb') as f:
                    data = stdout.read(1024*1024)
                    total = 0
                    while data:
                        f.write(data)
                        total += len(data)
                        data = stdout.read(1024*1024)
                
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", f"Yedeklendi:\n{local_path}"))
                self.parent.after(0, lambda: self.status_label.config(text="✅ Yedekleme tamamlandı", fg="green"))
                self.parent.after(0, lambda: self.progress_var.set(100))
            except Exception as e:
                self.parent.after(0, lambda: messagebox.showerror("Hata", f"Yedekleme hatası:\n{str(e)}"))
                self.parent.after(0, lambda: self.status_label.config(text="❌ Yedekleme hatası", fg="red"))
        
        threading.Thread(target=backup_thread, daemon=True).start()
    
    def get_frame(self):
        return self.frame