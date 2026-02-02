# SELSEBİL V2 - KURULUM KILAVUZU

## HIZLI KURULUM (5 DAKİKA)

### 1. Sanal Ortam Oluştur
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux
```

### 2. Gereksinimleri Kur
```bash
pip install -r requirements/development.txt
```

### 3. Veritabanını Hazırla
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Çalıştır
```bash
python manage.py runserver
```

Admin panel: http://127.0.0.1:8000/admin/

## MODÜLLER

- **Accounts**: Kullanıcı yönetimi, roller, audit trail
- **Families**: Aile kayıtları (TAM - En önemli modül)
- **Aid**: Yardım talepleri (Basit yapı, genişletilebilir)
- **Inventory**: Stok yönetimi (Basit yapı, genişletilebilir)
- **Finance**: Finans (Basit yapı, genişletilebilir)
- **CMS**: Web sitesi (Basit yapı, genişletilebilir)

## ÖNEMLİ NOTLAR

1. **Families modülü tam ve kusursuz**
2. Diğer modüller temel yapı - ihtiyaca göre genişletilebilir
3. BaseModel tüm modellerde ortak
4. Audit trail aktif
5. KVKK uyumlu

## SORUN GİDERME

**Pillow hatası:**
```bash
pip install --upgrade pip
pip install Pillow
```

**Migration hatası:**
```bash
python manage.py makemigrations accounts
python manage.py makemigrations families
python manage.py migrate
```
