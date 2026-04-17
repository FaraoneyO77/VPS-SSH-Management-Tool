import tkinter as tk
from tkinter import ttk, messagebox
import threading

class LogViewerModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.servers = []
        self.tail_active = False
        self.tail_thread = None
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        tk.Label(self.frame, text="📜 LOG İZLEYİCİ", font=("Arial", 12, "bold")).pack(pady=5)
        
        # Kontroller
        control_frame = tk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(control_frame, text="Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(control_frame, state="readonly", width=25)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        
        tk.Label(control_frame, text="Log Dosyası:").pack(side=tk.LEFT, padx=5)
        self.log_combo = ttk.Combobox(control_frame, state="readonly", width=25)
        self.log_combo['values'] = [
            "/var/log/syslog",
            "/var/log/auth.log",
            "/var/log/nginx/access.log",
            "/var/log/nginx/error.log",
            "/var/log/messages"
        ]
        self.log_combo.current(0)
        self.log_combo.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        btn_frame = tk.Frame(control_frame)
        btn_frame.pack(side=tk.LEFT, padx=10)
        
        self.view_btn = tk.Button(btn_frame, text="📄 Görüntüle", command=self.view_log)
        self.view_btn.pack(side=tk.LEFT, padx=2)
        
        self.tail_btn = tk.Button(btn_frame, text="▶ Canlı Takip (tail -f)", command=self.toggle_tail, bg="#4CAF50", fg="white")
        self.tail_btn.pack(side=tk.LEFT, padx=2)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹ Durdur", command=self.stop_tail, bg="#f44336", fg="white", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)
        
        # Satır sayısı
        tk.Label(control_frame, text="Satır:").pack(side=tk.LEFT, padx=5)
        self.lines_spinbox = tk.Spinbox(control_frame, from_=10, to=500, width=5)
        self.lines_spinbox.delete(0, tk.END)
        self.lines_spinbox.insert(0, "100")
        self.lines_spinbox.pack(side=tk.LEFT)
        
        # Log içeriği
        self.log_text = tk.Text(self.frame, bg="#1e1e1e", fg="#d4d4d4", font=("Consolas", 9), height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Arama
        search_frame = tk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(search_frame, text="🔍 Ara:").pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.search_log())
        
        self.search_count = tk.Label(search_frame, text="", font=("Arial", 8))
        self.search_count.pack(side=tk.LEFT, padx=5)
        
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
    
    def view_log(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        log_file = self.log_combo.get()
        lines = self.lines_spinbox.get()
        
        self.status_label.config(text=f"Log yükleniyor: {server['name']}...", fg="orange")
        self.log_text.delete(1.0, tk.END)
        
        def load_log():
            client = self.ssh.active_connections.get(server['name'])
            try:
                stdin, stdout, stderr = client.exec_command(f"tail -n {lines} {log_file} 2>/dev/null || echo 'Log dosyası bulunamadı'")
                log_content = stdout.read().decode('utf-8', errors='ignore')
                self.parent.after(0, lambda: self.log_text.insert(tk.END, log_content))
                self.parent.after(0, lambda: self.status_label.config(text=f"✅ {lines} satır yüklendi", fg="green"))
            except Exception as e:
                self.parent.after(0, lambda: self.status_label.config(text=f"❌ Hata: {str(e)}", fg="red"))
        
        threading.Thread(target=load_log, daemon=True).start()
    
    def toggle_tail(self):
        if not self.tail_active:
            self.start_tail()
        else:
            self.stop_tail()
    
    def start_tail(self):
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        self.tail_active = True
        self.tail_btn.config(text="⏸ Duraklat", bg="#FF9800", fg="white")
        self.stop_btn.config(state=tk.NORMAL)
        self.view_btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.status_label.config(text=f"Canlı takip: {server['name']}...", fg="orange")
        
        self.tail_thread = threading.Thread(target=self.tail_log, daemon=True)
        self.tail_thread.start()
    
    def tail_log(self):
        server = self.get_selected_server()
        log_file = self.log_combo.get()
        client = self.ssh.active_connections.get(server['name'])
        
        try:
            stdin, stdout, stderr = client.exec_command(f"tail -f {log_file} 2>/dev/null", timeout=None)
            while self.tail_active:
                line = stdout.readline()
                if line:
                    self.parent.after(0, lambda l=line: self.log_text.insert(tk.END, l))
                    self.parent.after(0, lambda: self.log_text.see(tk.END))
        except Exception as e:
            self.parent.after(0, lambda: self.status_label.config(text=f"❌ Takip hatası: {str(e)}", fg="red"))
    
    def stop_tail(self):
        self.tail_active = False
        self.tail_btn.config(text="▶ Canlı Takip (tail -f)", bg="#4CAF50", fg="white")
        self.stop_btn.config(state=tk.DISABLED)
        self.view_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Takip durduruldu", fg="gray")
    
    def search_log(self):
        search_term = self.search_entry.get()
        if not search_term:
            self.search_count.config(text="")
            return
        
        self.log_text.tag_remove("highlight", "1.0", tk.END)
        count = 0
        start = "1.0"
        
        while True:
            pos = self.log_text.search(search_term, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = f"{pos}+{len(search_term)}c"
            self.log_text.tag_add("highlight", pos, end)
            start = end
            count += 1
        
        self.log_text.tag_config("highlight", background="yellow", foreground="black")
        self.search_count.config(text=f"🔍 {count} bulundu", fg="green" if count > 0 else "red")
    
    def get_frame(self):
        return self.frame