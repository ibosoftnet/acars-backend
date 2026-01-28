# ACARS Backend
08.01.2026

---

## Giriş:

Havacılık Data Link iletilerini, ana yönlendirici veya doğrudan tek bir besleyiciden alıp alınan iletileri hem uç yazılıma aktaran hem de veri tabanına kaydeden, python tabanlı arka yazılım.

Ibosoft ATC sistemi içerisinde bu yazılım kullanılmaktadır. https://atc.ibosoft.net.tr

Yazılımın canlı aldığı veya veri tabanına kaydettiği verilerin görüntülenebilmesi için, web tabanlı uç yazılım ile birlikte kullanılmalıdır.

**Özellikler:**
* acarsdec ve acarshub yazılımlarının JSON formatını destekler.
* İletileri, uç yazılıma iletir.
* İletileri, MySQL türevi veri tabanına kaydeder.
* Veri bağlantısı koparsa, yeniden bağlanmayı kısa aralıklarla sürekli dener.
* Windows hizmeti olarak çalıştırılabilir.

**Data Link Yazılım Serisi:**
* ACARS Frontend
* ACARS Backend
* ACARS Decoding Library
* ACARS Tester

Havacılık iletişim ve data link sistemleri hakkında daha fazla bilgi için: https://egitim.ibosoft.net.tr/

**Lisans:**

Bu proje **Elastic License 2.0** ile lisanslanmıştır.

Kaynak kodu herkese açıktır. Kişisel ve ticari projelerde kullanım
serbesttir. Kod üzerinde değişiklik yapılabilir; ancak projenin
kendisi veya değiştirilmiş hâlleri, açık izin alınmadan yeniden
paylaşılamaz, yayımlanamaz veya bir servis olarak sunulamaz.


## Kurulum ve Çalıştırma:

### Gereklilikler:
- Windows işletim sistemi.
- Şu ek python paketleri:
  - mysql-connector-python==8.2.0
  - Flask==3.0.0
  - Flask-Cors==4.0.0

Python paketleri, requirements.txt dosyası aracılığıyla yüklenebilir:
```
pip install -r requirements.txt
```

### Kurulum:
Yazılım taşınabilirdir, indirip sunucuda uygun bir dizine yerleştiriniz.

### Çalıştırma:
Gerekli ayarları yaptıktan sonra start.bat dosyasını çalıştırınız. Kendiliğinden çalıştırma için bir görev zamanlaması oluşturuabilirsiniz. Ayrıca bat dosyası, doğrudan hizmet olarak çalıştırmaya uygun hazırlanmıştır. Uygun komutlar veya Servy gibi bir Windows hizmeti oluşturma aracı ile bat dosyasını çalıştıracak bir hizmet ekleyebilirsiniz.
> NOT: Henüz bağlantı kopukluk tespitinde bazı sorunlar bulunmaktadır ve uzun süreli çalışmalarda bazen kendiliğinden yeniden bağlanma özelliği çalışmamaktadır. Bu yüzden görev zamanlamasını veya hizmet ayarlarını, şimdilik görevin/himzetin günde 1-2 kere yeniden başlatılacağı şekilde yapınız.

---

## Ayarlarlamalar:

### Data Link Altyapısının Kurulması:
Yazılımın çalışabilmesi için, data link subnetwork'larının sinyallerini demodüle edip çözümledikten sonra, ACARS ağının iletilerini (Şu anlık ATN ağı desteklenmiyor.) uygun JSON biçiminde TCP sunucusu üzerinden iletebilen bir yazılımın kurulmuş ve çalışıyor olması gerekmektedir. Ayrıca ara bir yazılım ile birden fazla besleyiciden gelen iletiler tek bir TCP sunucusunda toplanıp sonra arka yazılıma iletilebilir.
* Birden fazla besleyiciden farklı protokollerle veri toplayıp TCP sunucusu olarak arka yazılıma veri iletmek için şu yazılımı kullanabilirsiniz: [acars_router](https://github.com/sdr-enthusiasts/acars_router)
  * acars_router, "TCP server" olarak ayarlanmalıdır.

Aşağıdaki yazılımlardan bazıları, doğrudan TCP ile iletim desteklemez ama acars_router veya başka bir aktarım yazılımı aracılığıyla veri sağlamada kullanılabilirler.

* VDL M0/A subnetwork'ü üzerinden ACARS ağı çözümlemek için: [acarsdec](https://github.com/f00b4r0/acarsdec)
* VDL M2 subnetwork'ü üzerinden ACARS ağı çözümlemek için: [vdlm2dec](https://github.com/TLeconte/vdlm2dec)
* HFDL subnetwork'ü üzerinden ACARS ağı çözümlemek için: [acarshfdl](https://github.com/szpajder/dumphfdl)
* INMARSAT Classic Aero subnetwork'ü üzerinden ACARS ağı çözümlemek için: [JAERO](https://github.com/jontio/JAERO)

Henüz desteklenmiyor ama ATN ağı için:
* VDL M2 subnetwork'ü üzerinden ATN ağı çözümlemek için: [dumpvdl2](https://github.com/szpajder/dumpvdl2)


### Yazılım Ayarları:
Kayıtlar için MySQL türevi bir veri tabanı sunucusu gereklidir ve içerisinde boş bir veri tabanı oluşturulmalıdır. Veri tabanının içerisine gerekli tablolar, yazılım tarafından eklenecektir.

Ayarlar, config.ini dosyası aracılığıyla yapılmaktadır. Ayarların açıklamaları şu şekildedir:

- [DATABASE]
  - host = MySQL türevi veri tabanı sunucusunun IP adresi (Ör: localhost)
  - port = Veri tabanı sunucusunun port numarası (Ör: 3306)
  - user = Veri tabanı kullanıcı adı.
  - password = Veri tabanı kullanıcı parolası.
  - database = Kullanılacak veri tabanının adı.
- [BACKEND]
  - host = Uç yazılımın bağlanabilmesi için web sunucusunun IP adresi (Ör: localhost)
  - port = Uç yazılımın bağlanabilmesi için web sunucusunun port numarası (Ör: 10002)
- [LISTENER]
  - host = İletileri yollayacak TCP sunucusunun IP adresi (Ör: localhost)
  - port = İletileri yollayacak TCP sunucusunun port numarası (Ör: 15551)
  - max_idle_time = Anlık bağlantı kopukluğu tespiti haricinde, yedek olarak bağlantı kopukluğu tespiti için izin verilen en uzun boşta kalma süresi (saniye cinsinden). Bu süre sonunda hala yeni bir ileti gelmemişse, yeniden bağlanma işlemi başlatılır. (Ör: 600)
- [RECORDING]
  - max_messages = Veri tabanında saklanacak azami ileti sayısı. Bu sayıya ulaşıldığında, en eski iletiler silinerek yeni iletiler kaydedilir. (Ör: 100000)
- [LOGGING]
  - max_log_size_mb = Log dosyasının azami boyutu (MB cinsinden) (Ör: 10)
  - backup_count = Log dosyası yedek sayısı (Ör: 2)
- [DECODING]
  - enabled = true veya false. ACARS ağı ARINC 622 uygulamalarının çözülmesi ile alkalı arka yazılım işlevelerinın etkinleştirilip etkinleştirilmeyeceğini belirler.

### Reverse Proxy Kullanımı:
Uç yazılım, yerel ağda değil de internet ortamında yayınlanacaksa ve de uç yazılımı ayarlarken doğrudan IP erişimi yerine alan adı kullanmak istiyorsanız Reverse Proxy kullanabilirsiniz. Uygun bir yazılım (IIS, Nginx, Apache vb.) ve ayarlamalar ile, dışarıdan belirli bir domain adı ve/veya alt alan adı ile gelen istekleri, arka yazılımın çalıştığı sunucu ve porta yönlendirebilirsiniz. Reverse Proxy ayarlanırken, SSE (Server-Sent Events) desteği olan bir yazılım kullanmanız ve SSE isteklerinin doğru şekilde yönlendirildiğinden emin olmanız gerekmektedir.

Örnek Nginx ayarı:
```
server {
        listen xxx.xxx.xxx.xxx:2053 ssl;   // nginx'in dinleyeceği IP adresi ve port
        server_name dlink-api.ibosoft.net.tr;    // Uç yazılıma erişim için kullanılacak alan adı

        ssl_certificate     ssl/cert.pem;   // SSL sertifikası (isteğe bağlı)
        ssl_certificate_key ssl/key.pem;    // SSL sertifikası anahtarı (isteğe bağlı)

        location ~ ^/error_docs/.*\.htm$ {
            root ./;
            internal;
        }

        // (İsteğe bağlı) Uç yazılımı yayınlayacağınız web sitesinin dışından erişimi zorlaştırmak için http_referer kontrolü, kendi alan adınızı ve arka yazılıma erişim için kullandığınız alan adını ekleyebilirsiniz. (Ör: atc.ibosoft.net.tr ve dlink-api.ibosoft.net.tr:2053)

        if ($http_referer !~ "^https://(atc\.ibosoft\.net\.tr|dlink-api\.ibosoft\.net\.tr(:2053)?)/") {
            return 403;
        }

        // SSE istekleri için gerekli ayarlar

        location / {
            proxy_pass http://127.0.0.1:10002;    // Arka yazılımın çalıştığı sunucu ve port ([BACKEND] ayarları), http:// ile SSL düşürme yazpılmıştır.
            proxy_http_version 1.1;

            # Önemli SSE ayarları:
            proxy_set_header Connection '';
            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 6h;
            proxy_send_timeout 60s;
            tcp_nodelay on;

            # SSE başlıkları
            add_header Cache-Control no-cache;
            add_header X-Accel-Buffering no;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
```

### Diğer Hususlar:
* Reverse Proxy ile birlikte Cloudflare proxy hizmetini kullanabilirsiniz. Cloudflare'ın ücretsiz planında proxy hizmetinden yararlanmak için desteklenen portlardan biri kullanılmalıdır. Örneğin 443 (varsayılan https portu), 2053, 2083, 2087, 2096 veya 8443 portları kullanılabilir. Reverse Proxy örneğinde 2053 portu kullanılmıştır.

---

## Yazılımın İşleyişi Hakkında Detaylar:

### JSON Yapısı:
Yazılım, TCP ile getirilem ASCII kodlu iletilerden JSON verisini ayrıştırır. Beklenen JSON yapısı örneği aşağıdaki gibidir:

```json
{
  "freq": 131.825,
  "channel": 1,
  "error": 0,
  "level": -36.2,
  "timestamp": 1760840065.479974,
  "app": {
    "name": "acarsdec",
    "ver": ""
  },
  "station_id": "ANTALYA1",
  "assstat": "skipped",
  "mode": "2",
  "label": "43",
  "block_id": "9",
  "ack": false,
  "tail": "TC-IBO",
  "text": "IBO8U,0214,00039,0000, 55,0226,N 37.078,E 30.527,",
  "msgno": "M37A",
  "flight": "IB008U"
}
```

**Açıklamaları:**

- `freq`: Frekans (MHz cinsinden)
- `channel`: Kanal numarası (Uç yazılımda işlevsiz)
- `error`: Hata durumu (0 = hata yok) (uç yazılımda işlevsiz)
- `level`: Sinyal seviyesi (dBm cinsinden)
- `timestamp`: İletinin içerisindeki zaman damgası (Unix epoch formatında) (Uç yazılımda işlevsiz.)
- `app`: İleti oluşturan uygulama bilgileri
  - `name`: Uygulama adı (Uç yazılım, uygulama türüne göre Subnetwork ve Network türünü belirler. Ayrıntılar için uç yazılımın rehberine bakınız.)
  - `ver`: Uygulama sürümü (Uç yazılımda işlevsiz.)
- `station_id`: İstasyon kimliği (Farklı alıcılara sahip kurulumlarda, alıcılara farklı istasyon kimlikleri atanabilir.)
- `assstat`: Çok bloklu ACARS iletilerinde, blokların ilişkilendirme durumu (Uç yazılımın rehberine bakınız.)
- `mode`: ACARS mesaj modu (Subnetwork türü değildir. VDL M0/A, M2 vs. ile karıştırmayın.) (Uç yazılımda işlevsiz.)
- `label`: ACARS mesaj Label'i
- `block_id`: ACARS mesaj Blok numarası
- `ack`: ACARS mesaj ACK bayrağı (true/false)
- `tail`: ARINC 618/620 Aircraft Address (Uçak kuyruk numarası)
- `text`: ACARS mesaj metin içeriği
- `msgno`: Downlink mesajları için ARINC 618/620 Downlink Squence Number (Uç yazılımda işlevsiz.)
- `flight`: ARINC 618/620 Flight Identifier

### Veritabanı Yapısı:
Yazılım, veri tabanında `messages_json_raw` adında bir tablo oluşturur ve iletileri bu tabloya kaydeder. Tablo yapısı, JSON yapısı ile uyumlu olacak şekilde ayarlanmıştır ve aşağıdaki gibidir:

| Sütun Adı       | Tür         | Açıklama                                      |
|-----------------|-------------|-----------------------------------------------|
| id              | INT (Auto Increment) | Birincil anahtar                     |
| received_at     | TIMESTAMP   | İletinin alındığı zaman                       |
| source_ip       | VARCHAR(45) | İletisinin kaynak IP adresi                   |
| source_port     | INT         | İletisinin kaynak portu                       |
| timestamp_msg   | DOUBLE      | İleti içerisindeki zaman damgası              |
| station_id      | VARCHAR(50) | İstasyon kimliği                              |
| channel         | INT         | Kanal numarası                                |
| freq            | DOUBLE      | Frekans                                       |
| level           | DOUBLE      | Sinyal seviyesi                               |
| error           | INT         | Hata durumu                                   |
| mode            | VARCHAR(10) | Mod                                           |
| label           | VARCHAR(20) | Label                                         |
| block_id        | VARCHAR(10) | Blok kimliği                                  |
| ack             | BOOLEAN     | ACK bayrağı                                   |
| tail            | VARCHAR(20) | Aircraft Address                              |
| text            | TEXT        | İleti metin içeriği                           |
| msgno           | VARCHAR(20) | Downlink Squence Numbe                        |
| flight          | VARCHAR(20) | Flight Identifier                             |
| assstat         | VARCHAR(50) | İlişkilendirme durumu                         |
| app_name        | VARCHAR(50) | Uygulama adı                                  |
| app_ver         | VARCHAR(50) | Uygulama sürümü                               |


### ARINC 620 ve ARINC 622 Uygulamalarının Çözülmesi:

* ACARS iletilerinin, ARINC 620 ve ICAO SARP'larına göre uygun uygulama (ACARS Application) türlerine göre sınıflandırılması, uç yazılım tarafından Ibosoft Acars Decoding Library ve uç yazılım içerisindeki bazı kodlar aracılığıyla yapılmaktadır.
* ARINC 620 dahilinde çözümlemnemsi verilen iletilerin/uygulamalarının çözümlenmesi, uç yazılım tarafında Ibosoft Acars Decoding Library aracılığıyla yapılmaktadır.
* Uç yazılımın; ACARS ağı üzerinden işleyen ARINC 622 uygulamalarının (ADS-C, CPDLC, MIAM ve bazı "H1" Label'li mühendislik iletileri) çözebilmesi için hazır bir kütüphane kullanılmıştır, derlenmiş DLL dosyası doğrudan projeye dahil edilmiştir. Bakınız: [libacars](https://github.com/szpajder/libacars)
* libacars, "SA" Label'li (Media Advisory) iletileri de çözebilmeketedir ancak bu Label'li iletilerin çözümlemesi, uç yazılım tarafında Ibosoft Acars Decoding Library ile yapılmaktadır.
* libacars Kütüphanesi'nin yapısı gereği, kütüphanein arka yazılıma dahil edilmesi kararı alınmıştır.
* ARINC 622 uygulamları çözülürken, canlı iletielr için, ileti ACARS ağı iletisi ise ve ileti Label'i AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1 ise ileti arka yazılımda çözülür ve canlı ileti bilgisiyle birlikte uç yazılıma iletilir.
* Geçmiş iletilerde, uç yazılım doğrudan PHP aracılığıyla veritabanına eriştiği için arka yazılımı doğrudan kullanmaz. ARINC 622 yazılımları ise arka yazılım atrafında çözümlemesi yapıldığı için, arka yazılıma bir API eklenmiştir. Uç yazılım, geçmiş iletiler için ARINC 622 uygulamalarını çözmek istediğinde, arka yazılıma bir istek gönderir ve arka yazılım iletiyi çözüp sonucu uç yazılıma iletir. Bu işlev için, iletini ACARS ağı iletisi ve ileti Label'inin AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1 olması gerekmektedir.


### Yeniden Bağlantı Denemesi:
Yazılım, TCP bağlantısı koptuğunda veya bağlantı kurulamadığında, kısa aralıklarla yeniden bağlanmayı dener. Yeniden bağlanma denemeleri sırasında, bağlantı kurulana kadar bekler ve bu sırada yeni iletiler alınamaz. Bağlantı kopukluğunun tespit edilememsi durumları için, ayarlarda belirtilen süre boyunca yeni bir ileti alınmazsa yeniden bağlanma işlemi başlatılır.

### Dosya Yapısı:
```
acars-backend/
├── main.py                 # Ana uygulama
├── database_handler.py     # Veritabanı işlemleri modülü
├── decode_handler.py       # ACARS mesaj çözücü (libacars sarmalayıcı)
├── tcp_client.py           # TCP istemci modülü
├── sse_server.py           # SSE sunucu modülü
├── config.ini              # Yapılandırma dosyası
├── requirements.txt        # Python bağımlılıkları
├── start.bat               # Windows başlatma betiği
├── LICENSE                 # Lisans dosyası
├── README.md               # Bu dosya
├── SSE_MIGRATION.md        # SSE geçiş dokümantasyonu
├── libacars/               # libacars kütüphane klasörü
│   ├── libacars-2.dll      # libacars ARINC 622 çözücü kütüphanesi
│   ├── zlib1.dll           # zlib sıkıştırma kütüphanesi (bağımlılık)
│   └── LICENSE.md          # libacars lisans dosyası
└── atc_datalink.log        # Log dosyası (Yazılım çalıştırılınca oluşturulur.)
```

---
