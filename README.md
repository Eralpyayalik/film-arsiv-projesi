# Film Arşiv

Film aramak, izlenecekleri biriktirmek ve kendi listelerini hazırlamak için yazdığım bir Flask uygulaması. Film bilgileri TMDB'den geliyor; hesaplar, favoriler, listeler ve yorumlar MySQL'de tutuluyor.

Film detaylarını açıp yorum bırakabiliyor, favorilerine ekleyebiliyor veya bir listeye kaydedebiliyorsun. Kullanıcı profilleri ve başka kullanıcıların listelerini görüntüleyen sayfalar da var.

## Yerelde çalıştırma

Bir Python sanal ortamında bağımlılıkları kur:

```sh
python -m pip install -r requirements.txt python-dotenv
```

`app.py`, ayarları `.env` dosyasından okuyabiliyor. Kendi bağlantı bilgilerinle şu alanları tanımla:

```dotenv
FLASK_SECRET_KEY=kendi_oturum_anahtarin
TMDB_API_KEY=kendi_tmdb_anahtarin
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=kendi_kullanicin
MYSQL_PASSWORD=kendi_parolan
MYSQL_DB=kendi_veritabanin
```

Veritabanındaki `users`, `comments`, `favorites` ve `user_lists` tablolarını ayrıca hazırlamak gerekiyor. Bu depoda hazır bir SQL kurulum dosyası yok.

```sh
python app.py
```

Uygulama `http://127.0.0.1:5000` adresinde açılır. Route'lar ve sorgular `app.py`, sayfa şablonları `templates` klasöründe.
