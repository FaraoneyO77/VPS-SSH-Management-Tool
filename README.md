# 🔌 RHEL VPS & SSH Manager Pro

**Birden fazla sunucuyu tek bir arayüzden yönetin!**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey.svg)]()

> SSH Manager Pro, birden fazla sunucuyu tek bir GUI arayüzünden yönetmenizi sağlayan kapsamlı bir araçtır. SSH key ile şifresiz bağlantı, dosya transferi, toplu komut gönderme ve daha fazlası...


---

## ✨ Özellikler

| Modül | Açıklama |
|-------|----------|
| 🖥️ **Terminal** | SSH ile şifresiz sunucu bağlantısı |
| 📁 **Dosya Gezgini** | Sunucudaki dosyaları görüntüleme, üst klasör desteği |
| 📤 **PC ↔ Sunucu** | Bilgisayar ile sunucu arasında dosya transferi |
| 🔄 **Sunucu → Sunucu** | İki sunucu arasında direkt dosya/klasör aktarımı |
| 💾 **Sunucu Backup** | Sunucular arası otomatik yedekleme |
| ⚡ **Toplu Komut** | Tüm sunuculara aynı anda komut gönderme |
| 📊 **İzleme** | CPU, RAM, Disk kullanımını tek panelden görme |
| 📜 **Log İzleyici** | Birden çok sunucunun loglarını canlı takip etme |
| 💻 **PC Backup** | Belirlenen klasörleri bilgisayara yedekleme |
| 🛠️ **Servisler** | systemctl komutlarını GUI'den yönetme |
| 🔥 **Firewall Yönetimi** | firewalld ile port, zone, rich rules, blacklist yönetimi |
| ☸️ **Kubernetes/K3s** | Node, Pod, Service, Deployment, Namespace yönetimi |

---

## 📦 Gereksinimler

| Gereksinim | Versiyon |
|------------|----------|
| Python | 3.8 veya üzeri |
| Paramiko | 3.0.0+ |
| Tkinter | Python ile gelir |
| Windows/Linux | İşletim sistemi |

---

## 🚀 Kurulum

### 1. Projeyi İndirin

```bash
git clone https://github.com/Faraoney077/VPS-SSH-Management-Tool
cd ssh-manager
```
### 2. Gerekli Kütüphaneleri Kurun

```pip install paramiko```

### 3. Uygulamayı Çalıştırın

```python3 main.py```

---

## ⚙️ Kullanım Kılavuzu

### 🔑 İlk Çalıştırma (SSH Key Oluşturma)

> Uygulama ilk çalıştığında otomatik olarak SSH anahtarı oluşturur. Anahtar şu konuma kaydedilir:

```C:\Users\KULLANICIADI\.ssh\id_ed25519```

### ➕ Sunucu Ekleme

1. Sol panelden **"➕ Ekle"** butonuna tıklayın
2. Sunucu bilgilerini girin:
   - **Sunucu Adı** (örnek: `Web Sunucu 1`)
   - **IP Adresi** (örnek: `192.168.1.100`)
   - **Kullanıcı** (varsayılan: `root`)
   - **Port** (varsayılan: `22`)
   - **Grup** (opsiyonel, örn: `Production`)
   - **Açıklama** (opsiyonel)
3. **"Kaydet ve Anahtar Yükle"** butonuna tıklayın
4. Sunucu şifrenizi girin (sadece **bir kere** sorulur)
5. Artık o sunucuya **şifresiz** bağlanabilirsiniz! 🎉

---

### 🔌 Sunucuya Bağlanma

| Yöntem | Açıklama |
|--------|----------|
| **Terminal sekmesi** | Sunucuyu seçin → **"🔌 Terminal Bağlan"** butonuna tıklayın |
| **Çift Tıklama** | Sol listede sunucuya çift tıklayın (Terminal sekmesinde bağlanır) |

> Yeni bir CMD penceresi açılır ve direkt olarak sunucuya bağlanırsınız.

---

### 📁 Dosya Gezgini ile Dolaşma

1. **"📁 Dosya Gezgini"** sekmesine gidin
2. Sunucuyu seçin ve **"Bağlan"** butonuna tıklayın
3. Klasörlere **çift tıklayarak** içine girin
4. **"📁 .. (Üst Klasör)"** butonu ile bir üst dizine çıkın
5. Dosyaya **sağ tıklayarak**:
   - **📥 İndir** → Dosyayı bilgisayarınıza kaydedin
   - **🗑️ Sil** → Dosyayı sunucudan silin

---

### 📤 Dosya Transferi (PC ↔ Sunucu)

#### PC'den Sunucuya Yükleme
1. **"📤 PC ↔ Sunucu"** sekmesine gidin
2. Sunucuyu seçin ve bağlanın
3. **"📤 Dosya Gönder"** butonuna tıklayın
4. Göndermek istediğiniz dosyayı seçin
5. Dosya otomatik olarak **şu an açık olduğunuz klasöre** yüklenir

#### Sunucudan PC'ye İndirme
1. **"📤 PC ↔ Sunucu"** sekmesine gidin
2. Dosya listesinden indirmek istediğiniz dosyaya **çift tıklayın**
3. Kaydetmek istediğiniz konumu seçin

---

### 🔄 Sunucular Arası Dosya Transferi

1. **"🔄 Sunucu → Sunucu"** sekmesine gidin
2. **Kaynak sunucu** (gönderen) ve **Hedef sunucu** (alan) seçin
3. Kaynak tarafta:
   - **Dosya seçmek için** → Dosyaya çift tıklayın (seçilir)
   - **Klasör içine girmek için** → Klasöre çift tıklayın
4. Hedef tarafta hedef klasöre gidin (çift tıklayarak)
5. **"🚀 SEÇİLEN ÖĞEYİ AKTAR"** butonuna tıklayın

> 📌 **Not:** Klasör aktarımı tüm alt klasörleri ve dosyalarıyla birlikte aktarır!

---

### ⚡ Toplu Komut Gönderme

1. **"⚡ Toplu Komut"** sekmesine gidin
2. **Ctrl tuşu** ile birden fazla sunucu seçin (veya "Tümünü Seç")
3. Komut kutusuna komutu yazın (örnekler: `uptime`, `df -h`, `free -m`)
4. **"🚀 Komut Gönder"** butonuna tıklayın
5. Tüm sunuculardan gelen yanıtları tek pencerede görün

> 💡 **İpucu:** Örnek komut butonları ile hızlıca komut gönderebilirsiniz.

---

### 📊 Sunucu İzleme

1. **"📊 İzleme"** sekmesine gidin
2. Sunucuyu seçin ve bağlanın
3. **"🔄 Yenile"** butonu ile anlık metrikleri görün:
   - **CPU Kullanımı** (yüzde ve çubuk)
   - **RAM Kullanımı** (yüzde ve çubuk)
   - **Disk Kullanımı** (yüzde ve çubuk)
   - **Load Average** (1, 5, 15 dakika)
   - **Çalışma Süresi** (uptime)
4. **"▶ Otomatik Yenile"** butonu ile 5 saniyede bir otomatik güncelleme yapın

---

### 📜 Log İzleyici

1. **"📜 Log İzleyici"** sekmesine gidin
2. Sunucuyu ve log dosyasını seçin:
   - `/var/log/syslog` → Sistem logları
   - `/var/log/auth.log` → Kimlik doğrulama logları
   - `/var/log/nginx/access.log` → Nginx erişim logları
   - `/var/log/nginx/error.log` → Nginx hata logları
3. **"📄 Görüntüle"** ile son 100 satırı gösterin
4. **"▶ Canlı Takip (tail -f)"** ile logları gerçek zamanlı izleyin
5. **🔍 Arama kutusu** ile log içinde arama yapın

---

### 💾 PC Backup (Bilgisayara Yedekleme)

1. **"💻 PC Backup"** sekmesine gidin
2. **"➕ Yeni Görev"** ile backup görevi oluşturun:
   - **Sunucu:** Hangi sunucudan yedek alınacak
   - **Kaynak Klasör:** Sunucudaki hangi klasör yedeklenecek (örn: `/etc`)
   - **Yerel Hedef:** Bilgisayarınızda nereye kaydedilecek
   - **Zamanlama:** Hangi saatte yedeklensin (örn: `3` → saat 03:00)
3. **"▶ Şimdi Çalıştır"** ile hemen yedek alın
4. Yedekler otomatik olarak `sunucu_adi_klasor_adi_tarih.tar.gz` formatında kaydedilir

---

### 🛠️ Servis Yönetimi (systemctl)

1. **"🛠️ Servisler"** sekmesine gidin
2. Sunucuyu seçin ve **"🔄 Servisleri Listele"** butonuna tıklayın
3. Servis listesinden bir servis seçin:
   - **▶ Başlat** → Servisi başlatır (`systemctl start`)
   - **⏹ Durdur** → Servisi durdurur (`systemctl stop`)
   - **🔄 Yeniden Başlat** → Servisi yeniden başlatır (`systemctl restart`)
   - **✅ Enable** → Servisin otomatik başlamasını sağlar
   - **❌ Disable** → Servisin otomatik başlamasını engeller
   - **📋 Durum** → Servisin detaylı durumunu gösterir
4. **🔍 Arama kutusu** ile servisleri filtreleyin

---

### 🔥 Firewall Yönetimi

1. **"🔥 Firewall"** sekmesine gidin
2. Sunucuyu seçin ve bağlanın (firewall durumu otomatik yüklenir)

#### Port Açma
| Alan | Açıklama | Örnek |
|------|----------|-------|
| Port Numarası | Açılacak port | `8080` veya `8000-8100` |
| Protokol | TCP veya UDP | `tcp` |
| Zone | Güvenlik bölgesi | `public` |
| Kaynak IP | Sadece bu IP'den erişim (opsiyonel) | `192.168.1.100` |
| Kalıcı | Sunucu yeniden başlasa da açık kalsın | ✅ işaretli |

#### Gelişmiş Kurallar (Rich Rules)
| Kural Tipi | Açıklama |
|------------|----------|
| **IP Engelle** | Belirtilen IP'yi tamamen engeller |
| **IP İzin** | Sadece belirtilen IP'ye izin verir |
| **Port Limiti** | Porta belirli sayıda istek limiti koyar (örn: 10/s) |
| **Zamanlı Engelle** | Belirtilen saat aralığında IP'yi engeller |
| **Özel Kural** | İstediğiniz formatta kural yazabilirsiniz |

#### Blacklist
- Engellenen IP'leri listeler
- **"🚫 IP Ekle"** ile yeni IP engelleyebilirsiniz
- **"✅ Engeli Kaldır"** ile engeli kaldırabilirsiniz

> ⚠️ **Uyarı:** Değişiklikleri kalıcı yapmak için **"💾 Permanent Kaydet"** butonunu kullanmayı unutmayın!

---

### ☸️ Kubernetes/K3s Yönetimi

1. **"☸️ Kubernetes"** sekmesine gidin
2. Sunucuyu seçin (K3s kurulu olmalı)

#### K3s Kurulumu
- **"📦 K3s Kur"** butonu ile otomatik kurulum yapın
- Kurulum 1-2 dakika sürer

#### Node Yönetimi
| İşlem | Açıklama |
|-------|----------|
| **🏷️ Label Ekle** | Node'a etiket ekler (`disktype=ssd`) |
| **⛔ Cordon** | Node'u geçici olarak devre dışı bırakır |
| **✅ Uncordon** | Node'u tekrar aktif eder |
| **🗑️ Drain** | Node'daki tüm pod'ları başka node'lara taşır |

#### Pod Yönetimi
- Pod'ları listeler (namespace filtresi ile)
- **"📋 Log Göster"** → Pod loglarını görüntüler
- **"🐚 Shell Aç"** → Pod içinde terminal açar
- **"🗑️ Pod Sil"** → Pod'u siler
- **"🔄 Restart"** → Pod'u yeniden başlatır

#### Deployment Yönetimi
- Deployment'ları listeler
- **"📈 Scale"** → Replica sayısını değiştirir
- **"🔄 Restart"** → Deployment'ı yeniden başlatır
- **"📋 Status"** → Deployment durumunu gösterir

#### Namespace Yönetimi
- Tüm namespace'leri listeler
- **"➕ Namespace Ekle"** → Yeni namespace oluşturur
- **"🗑️ Namespace Sil"** → Namespace'i ve içindeki her şeyi siler

---

## ⌨️ Kısayollar

| Kısayol | İşlev |
|---------|-------|
| `Çift Tıklama` | Klasör içine girme / Dosya seçme / Sunucuya bağlanma |
| `Sağ Tıklama` | Dosya menüsü (İndir / Sil) |
| `Ctrl + Çoklu Seçim` | Toplu komut için birden fazla sunucu seçme |

---

## 🔧 Sık Karşılaşılan Sorunlar ve Çözümleri

| Sorun | Çözüm |
|-------|-------|
| `ssh-keygen` bulunamıyor | PowerShell'i **Yönetici olarak** çalıştırın |
| Bağlantı reddediliyor | Sunucuda SSH servisinin çalıştığından emin olun |
| Anahtar yüklenemiyor | Sunucu şifresini doğru girdiğinizden emin olun |
| "Host key verification failed" | `known_hosts` dosyasından eski kaydı silin |
| Klasör aktarımı çalışmıyor | Hedef klasörün yazma izni olduğunu kontrol edin |
| Firewall komutları çalışmıyor | Sunucuda firewalld kurulu mu? `systemctl status firewalld` ile kontrol edin |
| K3s kurulumu başarısız | İnternet bağlantısını kontrol edin, tekrar deneyin |

---

## 📁 Proje Yapısı

```bash
ssh-manager/
│
├── main.py                 # Ana uygulama
├── core/
│   ├── ssh_client.py       # SSH bağlantı yöneticisi
│   └── key_manager.py      # SSH key oluşturma/yükleme
├── modules/
│   ├── terminal.py         # Terminal bağlantısı
│   ├── file_browser.py     # Dosya gezgini
│   ├── file_transfer.py    # PC ↔ Sunucu dosya transferi
│   ├── server_transfer.py  # Sunucu → Sunucu transfer
│   ├── server_backup.py    # Sunucular arası yedekleme
│   ├── bulk_commands.py    # Toplu komut gönderme
│   ├── monitoring.py       # CPU/RAM/Disk izleme
│   ├── log_viewer.py       # Log izleyici
│   ├── backup.py           # PC'ye yedekleme
│   ├── service_manager.py  # systemctl servis yönetimi
│   ├── firewall_manager.py # firewalld yönetimi
│   └── k8s_manager.py      # Kubernetes/K3s yönetimi
└── data/
    └── servers.json        # (otomatik oluşur)
```

---

## 🤝 Katkıda Bulunma

1. Bu repoyu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/yeniOzellik`)
3. Değişikliklerinizi commit edin (`git commit -m 'Yeni özellik eklendi'`)
4. Branch'inizi push edin (`git push origin feature/yeniOzellik`)
5. Pull Request oluşturun

---

## 📄 Lisans

Bu proje GNU lisansı ile lisanslanmıştır.

---

## 👨‍💻 Yazar

**Cihan Dik**

- GitHub: [@FaraoneyO77](https://github.com/FaraoneyO77)

---

## ⭐ Beğendiniz mi?

Projeyi beğendiyseniz ⭐ yıldız vermeyi unutmayın!

---

**Made with ❤️ for DevOps**
