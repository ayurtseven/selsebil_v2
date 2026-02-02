# SELSEBİL V2  
**Enterprise-Grade NGO / Charity Management System**

SELSEBİL V2, sivil toplum kuruluşları (STK), dernekler ve yardım organizasyonları için geliştirilmiş,  
**uçtan uca yardım yönetimi**, **finansal takip**, **stok kontrolü** ve **kurumsal web içerik yönetimi** sağlayan
**modüler ve production-ready** bir Django tabanlı sistemdir.

Bu proje; sahadaki gerçek STK operasyonları dikkate alınarak tasarlanmış olup,  
basit CRUD uygulamalarının ötesinde **iş akışı, denetim (audit) ve veri bütünlüğü** odaklıdır.

---

## 🎯 Amaç

- Aile ve hane bazlı yardım takibi
- Yardım taleplerinin uçtan uca yönetimi
- Stok ve bağış hareketlerinin otomatik kontrolü
- Finansal işlemlerin muhasebe mantığıyla izlenmesi
- Kurumsal web sitesi içeriklerinin yönetimi
- Yetki, denetim ve şeffaflık odaklı yapı

---

## 👥 Hedef Kullanıcılar

- Dernekler
- Vakıflar
- İnsani yardım organizasyonları
- Sosyal sorumluluk projeleri yürüten kurumlar
- Kurumsal STK yazılımı geliştirmek isteyen ekipler

---

## 🧱 Teknik Mimari

- **Backend:** Django (Modüler App-Based Mimari)
- **Frontend:** Planlı (React)
- **Database:**  
  - Development: SQLite  
  - Production: PostgreSQL
- **Config Yönetimi:** Ortam bazlı (`base / development / production`)
- **Güvenlik:** Audit trail, rol bazlı yetkilendirme, veri bütünlüğü

---

## 📦 Modüller

| Modül | Açıklama |
|-----|---------|
| **Accounts** | Özel kullanıcı modeli, roller ve audit log |
| **Families** | Aile ve hane yönetimi (ana modül) |
| **Aid** | Yardım talepleri, onay ve dağıtım süreçleri |
| **Inventory** | Stok, bağışçı ve stok hareketleri |
| **Finance** | Nakit yardımlar, askıda faturalar, bütçe |
| **CMS** | Kurumsal web sitesi içerik yönetimi |

---

## ⭐ Öne Çıkan Özellikler

- ✔️ **Modüler mimari** (Enterprise Django standardı)
- ✔️ **Audit Trail** (Kim, neyi, ne zaman yaptı?)
- ✔️ **Silinemez finans & stok kayıtları**
- ✔️ **Soft delete** ile veri bütünlüğü
- ✔️ **Otomatik transaction ve stok güncellemeleri**
- ✔️ **Singleton pattern** (Site ayarları)
- ✔️ **Rol bazlı yetkilendirme**
- ✔️ **Gerçek STK operasyonlarına uygun iş akışları**

---

## 🔐 Güvenlik & Veri Bütünlüğü

- Rol bazlı erişim kontrolü
- AuditLog ile tam denetim izi
- Finans ve stok hareketleri **silinemez**
- Soft delete yaklaşımı
- Django’nun CSRF & XSS korumaları
- KVKK uyumlu veri yaklaşımı

---

## 🚀 Kurulum (Geliştirme Ortamı)

```bash
# Repo'yu klonla
git clone https://github.com/ayurtseven/selsebil_v2.git
cd selsebil_v2

# Sanal ortam
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Linux / Mac

# Bağımlılıklar
pip install -r requirements/development.txt

# Veritabanı
python manage.py migrate

# Superuser
python manage.py createsuperuser

# Çalıştır
python manage.py runserver
