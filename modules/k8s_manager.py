import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

class K8sManagerModule:
    def __init__(self, parent, ssh_manager):
        self.parent = parent
        self.ssh = ssh_manager
        self.current_server = None
        self.nodes = []
        self.pods = []
        self.services = []
        self.deployments = []
        
        self.setup_ui()
    
    def setup_ui(self):
        self.frame = tk.Frame(self.parent)
        
        # Başlık
        tk.Label(self.frame, text="☸️ KUBERNETES/K3s YÖNETİMİ", 
                font=("Arial", 12, "bold"), fg="#326CE5").pack(pady=5)
        
        # Sunucu seçimi
        server_frame = tk.Frame(self.frame)
        server_frame.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Label(server_frame, text="Master Sunucu:").pack(side=tk.LEFT, padx=5)
        self.server_combo = ttk.Combobox(server_frame, state="readonly", width=35)
        self.server_combo.pack(side=tk.LEFT, padx=5)
        self.server_combo.bind("<<ComboboxSelected>>", self.load_cluster_status)
        
        self.refresh_btn = tk.Button(server_frame, text="🔄 Yenile", command=self.load_cluster_status)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.install_btn = tk.Button(server_frame, text="📦 K3s Kur", command=self.install_k3s,
                                      bg="#4CAF50", fg="white")
        self.install_btn.pack(side=tk.LEFT, padx=5)
        
        # Ana notebook
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)
        
        # Sekme 1: Nodes
        self.node_frame = tk.Frame(self.notebook)
        self.notebook.add(self.node_frame, text="🖥️ Nodes")
        self.setup_node_tab()
        
        # Sekme 2: Pods
        self.pod_frame = tk.Frame(self.notebook)
        self.notebook.add(self.pod_frame, text="📦 Pods")
        self.setup_pod_tab()
        
        # Sekme 3: Services
        self.service_frame = tk.Frame(self.notebook)
        self.notebook.add(self.service_frame, text="🔌 Services")
        self.setup_service_tab()
        
        # Sekme 4: Deployments
        self.deploy_frame = tk.Frame(self.notebook)
        self.notebook.add(self.deploy_frame, text="🚀 Deployments")
        self.setup_deploy_tab()
        
        # Sekme 5: Namespaces
        self.ns_frame = tk.Frame(self.notebook)
        self.notebook.add(self.ns_frame, text="📁 Namespaces")
        self.setup_namespace_tab()
        
        # Durum
        self.status_label = tk.Label(self.frame, text="Hazır - Master sunucu seçin", font=("Arial", 8), fg="gray")
        self.status_label.pack(fill=tk.X)
    
    def setup_node_tab(self):
        """Node listesi sekmesi"""
        columns = ("Node", "Durum", "Roller", "Yaş", "Versiyon", "IP")
        self.node_tree = ttk.Treeview(self.node_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.node_tree.heading(col, text=col)
            self.node_tree.column(col, width=120)
        
        self.node_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Node işlemleri
        btn_frame = tk.Frame(self.node_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="🏷️ Label Ekle", command=self.add_node_label,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="⛔ Node Cordon", command=self.cordon_node,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="✅ Node Uncordon", command=self.uncordon_node,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Node Drain", command=self.drain_node,
                 bg="#FF5722", fg="white").pack(side=tk.LEFT, padx=2)
    
    def setup_pod_tab(self):
        """Pod listesi sekmesi"""
        # Namespace filtresi
        filter_frame = tk.Frame(self.pod_frame)
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Namespace:").pack(side=tk.LEFT, padx=5)
        self.namespace_combo = ttk.Combobox(filter_frame, state="readonly", width=20)
        self.namespace_combo.pack(side=tk.LEFT, padx=5)
        self.namespace_combo.bind("<<ComboboxSelected>>", lambda e: self.load_pods())
        
        tk.Button(filter_frame, text="🔄 Podları Yenile", command=self.load_pods,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        
        columns = ("Pod", "Durum", "Restarts", "Yaş", "Node", "IP")
        self.pod_tree = ttk.Treeview(self.pod_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.pod_tree.heading(col, text=col)
            self.pod_tree.column(col, width=120)
        
        self.pod_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Pod işlemleri
        btn_frame = tk.Frame(self.pod_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="📋 Log Göster", command=self.show_pod_logs,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🐚 Shell Aç", command=self.pod_shell,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Pod Sil", command=self.delete_pod,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔄 Restart", command=self.restart_pod,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
    
    def setup_service_tab(self):
        """Service listesi sekmesi"""
        columns = ("Service", "Type", "Cluster-IP", "External-IP", "Ports", "Age")
        self.service_tree = ttk.Treeview(self.service_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.service_tree.heading(col, text=col)
            self.service_tree.column(col, width=130)
        
        self.service_tree.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def setup_deploy_tab(self):
        """Deployment listesi sekmesi"""
        columns = ("Deployment", "Ready", "Up-to-date", "Available", "Age", "Containers")
        self.deploy_tree = ttk.Treeview(self.deploy_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.deploy_tree.heading(col, text=col)
            self.deploy_tree.column(col, width=120)
        
        self.deploy_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Deployment işlemleri
        btn_frame = tk.Frame(self.deploy_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="📈 Scale", command=self.scale_deployment,
                 bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🔄 Restart", command=self.restart_deployment,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="📋 Status", command=self.deployment_status,
                 bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=2)
    
    def setup_namespace_tab(self):
        """Namespace yönetimi sekmesi"""
        self.ns_listbox = tk.Listbox(self.ns_frame, height=15, font=("Consolas", 9))
        self.ns_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        btn_frame = tk.Frame(self.ns_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="➕ Namespace Ekle", command=self.add_namespace,
                 bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="🗑️ Namespace Sil", command=self.delete_namespace,
                 bg="#f44336", fg="white").pack(side=tk.LEFT, padx=2)
    
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
    
    def run_kubectl(self, command):
        """kubectl komutu çalıştır"""
        server = self.get_selected_server()
        if not server or not self.ssh.is_connected(server['name']):
            return None
        
        client = self.ssh.active_connections.get(server['name'])
        stdin, stdout, stderr = client.exec_command(f"kubectl {command} 2>/dev/null || echo 'ERROR'")
        return stdout.read().decode().strip()
    
    def install_k3s(self):
        """K3s kurulumu yap"""
        server = self.get_selected_server()
        if not server:
            messagebox.showwarning("Uyarı", "Lütfen bir sunucu seçin!")
            return
        
        if not self.ssh.is_connected(server['name']):
            messagebox.showwarning("Uyarı", f"Önce {server['name']} sunucusuna bağlanın!")
            return
        
        if messagebox.askyesno("K3s Kurulumu", 
                               f"'{server['name']}' sunucusuna K3s kurulacak.\n\nDevam etmek istiyor musunuz?"):
            self.status_label.config(text="K3s kuruluyor... Bu 1-2 dakika sürebilir.", fg="orange")
            
            def install():
                client = self.ssh.active_connections.get(server['name'])
                stdin, stdout, stderr = client.exec_command("curl -sfL https://get.k3s.io | sh -")
                output = stdout.read().decode()
                
                self.parent.after(0, lambda: self.load_cluster_status())
                self.parent.after(0, lambda: self.status_label.config(text="✅ K3s kuruldu", fg="green"))
                self.parent.after(0, lambda: messagebox.showinfo("Başarılı", "K3s başarıyla kuruldu!"))
            
            threading.Thread(target=install, daemon=True).start()
    
    def load_cluster_status(self):
        """Cluster durumunu yükle"""
        server = self.get_selected_server()
        if not server:
            return
        
        if not self.ssh.is_connected(server['name']):
            # K3s kurulu mu kontrol et
            client = self.ssh.active_connections.get(server['name'])
            stdin, stdout, stderr = client.exec_command("which kubectl")
            if not stdout.read().decode().strip():
                self.status_label.config(text="⚠️ K3s kurulu değil. 'K3s Kur' butonuna tıklayın.", fg="orange")
                return
        
        self.current_server = server
        self.status_label.config(text="Cluster bilgileri yükleniyor...", fg="orange")
        
        def load():
            # Nodes
            nodes_output = self.run_kubectl("get nodes -o wide --no-headers")
            self.nodes = []
            if nodes_output and nodes_output != "ERROR":
                for line in nodes_output.split('\n'):
                    if line.strip():
                        parts = line.split()
                        self.nodes.append({
                            'name': parts[0],
                            'status': parts[1],
                            'roles': parts[2] if len(parts) > 2 else '<none>',
                            'age': parts[3] if len(parts) > 3 else '-',
                            'version': parts[4] if len(parts) > 4 else '-',
                            'ip': parts[5] if len(parts) > 5 else '-'
                        })
            
            # Namespaces
            ns_output = self.run_kubectl("get namespaces -o name --no-headers")
            self.namespaces = [ns.replace('namespace/', '') for ns in ns_output.split('\n') if ns] if ns_output else ["default"]
            
            # Services
            svc_output = self.run_kubectl("get services --all-namespaces -o wide --no-headers")
            self.services = []
            if svc_output and svc_output != "ERROR":
                for line in svc_output.split('\n'):
                    if line.strip():
                        parts = line.split()
                        self.services.append({
                            'namespace': parts[0],
                            'name': parts[1],
                            'type': parts[2],
                            'cluster_ip': parts[3],
                            'external_ip': parts[4] if len(parts) > 4 else '<none>',
                            'ports': parts[5] if len(parts) > 5 else '-',
                            'age': parts[6] if len(parts) > 6 else '-'
                        })
            
            # Deployments
            deploy_output = self.run_kubectl("get deployments --all-namespaces --no-headers")
            self.deployments = []
            if deploy_output and deploy_output != "ERROR":
                for line in deploy_output.split('\n'):
                    if line.strip():
                        parts = line.split()
                        self.deployments.append({
                            'namespace': parts[0],
                            'name': parts[1],
                            'ready': parts[2],
                            'up_to_date': parts[3],
                            'available': parts[4],
                            'age': parts[5],
                            'containers': parts[6] if len(parts) > 6 else '-'
                        })
            
            self.parent.after(0, self.update_cluster_ui)
            self.parent.after(0, lambda: self.status_label.config(text="✅ Cluster bilgileri yüklendi", fg="green"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def update_cluster_ui(self):
        """Cluster UI'ını güncelle"""
        # Node listesi
        self.node_tree.delete(*self.node_tree.get_children())
        for node in self.nodes:
            self.node_tree.insert("", tk.END, values=(
                node['name'], node['status'], node['roles'], node['age'], node['version'], node['ip']
            ))
        
        # Namespace listesi
        self.ns_listbox.delete(0, tk.END)
        for ns in self.namespaces:
            self.ns_listbox.insert(tk.END, ns)
        
        # Namespace combobox
        self.namespace_combo['values'] = self.namespaces
        if self.namespaces:
            self.namespace_combo.current(0)
        
        # Service listesi
        self.service_tree.delete(*self.service_tree.get_children())
        for svc in self.services:
            self.service_tree.insert("", tk.END, values=(
                svc['name'], svc['type'], svc['cluster_ip'], svc['external_ip'], svc['ports'], svc['age']
            ))
        
        # Deployment listesi
        self.deploy_tree.delete(*self.deploy_tree.get_children())
        for deploy in self.deployments:
            self.deploy_tree.insert("", tk.END, values=(
                deploy['name'], deploy['ready'], deploy['up_to_date'], deploy['available'], deploy['age'], deploy['containers']
            ))
        
        self.load_pods()
    
    def load_pods(self):
        """Pod'ları yükle"""
        namespace = self.namespace_combo.get()
        if not namespace:
            return
        
        pods_output = self.run_kubectl(f"get pods -n {namespace} -o wide --no-headers")
        
        self.pod_tree.delete(*self.pod_tree.get_children())
        
        if pods_output and pods_output != "ERROR":
            for line in pods_output.split('\n'):
                if line.strip():
                    parts = line.split()
                    self.pod_tree.insert("", tk.END, values=(
                        parts[0], parts[2] if len(parts) > 2 else '-', 
                        parts[3] if len(parts) > 3 else '-', parts[4] if len(parts) > 4 else '-',
                        parts[6] if len(parts) > 6 else '-', parts[5] if len(parts) > 5 else '-'
                    ))
    
    def add_node_label(self):
        selection = self.node_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir node seçin!")
            return
        
        node = self.node_tree.item(selection[0])['values'][0]
        label = simpledialog.askstring("Label Ekle", "Label girin (örn: disktype=ssd):")
        if label:
            self.run_kubectl(f"label nodes {node} {label}")
            self.load_cluster_status()
    
    def cordon_node(self):
        selection = self.node_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir node seçin!")
            return
        node = self.node_tree.item(selection[0])['values'][0]
        self.run_kubectl(f"cordon {node}")
        self.load_cluster_status()
    
    def uncordon_node(self):
        selection = self.node_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir node seçin!")
            return
        node = self.node_tree.item(selection[0])['values'][0]
        self.run_kubectl(f"uncordon {node}")
        self.load_cluster_status()
    
    def drain_node(self):
        selection = self.node_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir node seçin!")
            return
        node = self.node_tree.item(selection[0])['values'][0]
        if messagebox.askyesno("Drain Node", f"Node '{node}' drain edilsin mi? Podlar başka node'lara taşınacak."):
            self.run_kubectl(f"drain {node} --ignore-daemonsets --delete-emptydir-data")
            self.load_cluster_status()
    
    def show_pod_logs(self):
        selection = self.pod_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir pod seçin!")
            return
        pod = self.pod_tree.item(selection[0])['values'][0]
        namespace = self.namespace_combo.get()
        
        logs = self.run_kubectl(f"logs -n {namespace} {pod} --tail=100")
        
        log_window = tk.Toplevel(self.frame)
        log_window.title(f"Pod Logs: {pod}")
        log_window.geometry("800x500")
        
        text_widget = tk.Text(log_window, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, logs)
    
    def pod_shell(self):
        selection = self.pod_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir pod seçin!")
            return
        pod = self.pod_tree.item(selection[0])['values'][0]
        namespace = self.namespace_combo.get()
        
        import subprocess
        subprocess.Popen(f'start cmd /k "kubectl exec -it -n {namespace} {pod} -- /bin/bash"', shell=True)
    
    def delete_pod(self):
        selection = self.pod_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir pod seçin!")
            return
        pod = self.pod_tree.item(selection[0])['values'][0]
        namespace = self.namespace_combo.get()
        
        if messagebox.askyesno("Pod Sil", f"Pod '{pod}' silinsin mi?"):
            self.run_kubectl(f"delete pod -n {namespace} {pod}")
            self.load_pods()
    
    def restart_pod(self):
        selection = self.pod_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir pod seçin!")
            return
        pod = self.pod_tree.item(selection[0])['values'][0]
        namespace = self.namespace_combo.get()
        
        self.run_kubectl(f"delete pod -n {namespace} {pod}")
        self.load_pods()
        self.status_label.config(text=f"Pod {pod} yeniden başlatılıyor...", fg="orange")
    
    def scale_deployment(self):
        selection = self.deploy_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir deployment seçin!")
            return
        deploy = self.deploy_tree.item(selection[0])['values'][0]
        namespace = "default"
        
        replica = simpledialog.askinteger("Scale", f"{deploy} kaç replica olsun?", initialvalue=1, minvalue=0, maxvalue=100)
        if replica is not None:
            self.run_kubectl(f"scale deployment {deploy} -n {namespace} --replicas={replica}")
            self.load_cluster_status()
    
    def restart_deployment(self):
        selection = self.deploy_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir deployment seçin!")
            return
        deploy = self.deploy_tree.item(selection[0])['values'][0]
        namespace = "default"
        
        self.run_kubectl(f"rollout restart deployment {deploy} -n {namespace}")
        self.status_label.config(text=f"Deployment {deploy} yeniden başlatılıyor...", fg="orange")
    
    def deployment_status(self):
        selection = self.deploy_tree.selection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir deployment seçin!")
            return
        deploy = self.deploy_tree.item(selection[0])['values'][0]
        namespace = "default"
        
        status = self.run_kubectl(f"rollout status deployment {deploy} -n {namespace}")
        messagebox.showinfo(f"{deploy} Durumu", status)
    
    def add_namespace(self):
        ns = simpledialog.askstring("Namespace Ekle", "Namespace adı girin:")
        if ns:
            self.run_kubectl(f"create namespace {ns}")
            self.load_cluster_status()
    
    def delete_namespace(self):
        selection = self.ns_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir namespace seçin!")
            return
        ns = self.ns_listbox.get(selection[0])
        if ns in ["default", "kube-system", "kube-public"]:
            messagebox.showerror("Hata", "Sistem namespace'i silinemez!")
            return
        if messagebox.askyesno("Namespace Sil", f"Namespace '{ns}' ve içindeki her şey silinecek!\nDevam etmek istiyor musunuz?"):
            self.run_kubectl(f"delete namespace {ns}")
            self.load_cluster_status()
    
    def get_frame(self):
        return self.frame