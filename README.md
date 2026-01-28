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

**Data Link Yazılımlarımız:**
* ACARS Viewer
* ACARS Backend
* ACARS Decoding Library
* ACARS Tester

> Havacılık iletişim ve data link sistemleri hakkında daha fazla bilgi için: https://egitim.ibosoft.net.tr/  
> Projede kullanılan kısaltmalar için bakınız: [Ibosoft Kısaltmalar Veri Tabanı](https://egitim.ibosoft.net.tr/abbreviations-database/)

**Lisans:**

Bu proje **Elastic License 2.0** ile lisanslanmıştır.

Kaynak kodu herkese açıktır. Kişisel ve ticari projelerde kullanım
serbesttir. Kod üzerinde değişiklik yapılabilir; ancak projenin
kendisi veya değiştirilmiş hâlleri, açık izin alınmadan yeniden
paylaşılamaz, yayımlanamaz veya bir servis olarak sunulamaz.

---

## Introduction:

A Python-based backend software that receives aviation Data Link messages from a main router or directly from a single feeder and forwards the received messages to both the frontend software and records them to a database.

This software is used within the Ibosoft ATC system. https://atc.ibosoft.net.tr

To view the data that the software receives live or stores in the database, it must be used together with the web-based frontend software.

**Features:**
* Supports JSON format of acarsdec and acarshub software.
* Forwards messages to frontend software.
* Records messages to MySQL-based database.
* If connection is lost, continuously retries reconnection at short intervals.
* Can be run as a Windows service.

**Our Data Link Software Series:**
* ACARS Viewer
* ACARS Backend
* ACARS Decoding Library
* ACARS Tester

> For more information about aviation communication and data link systems: https://egitim.ibosoft.net.tr/  
> For abbreviations used in the project, see: [Ibosoft Abbreviations Database](https://egitim.ibosoft.net.tr/abbreviations-database/)

**License:**

This project is licensed under **Elastic License 2.0**.

The source code is publicly available. Use in personal and commercial projects
is free. The code can be modified; however, the project itself or its modified versions
cannot be redistributed, published, or offered as a service without explicit permission.


## Kurulum ve Çalıştırma:

### Gereklilikler:
- Windows işletim sistemi.
- Python 3.x
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
Gerekli ayarları yaptıktan sonra start.bat betik dosyasını çalıştırınız. Kendiliğinden çalıştırma için bir görev zamanlaması oluşturabilirsiniz.
* Bat betiği, doğrudan hizmet olarak çalıştırmaya uygun hazırlanmıştır. Uygun komutlar veya Servy gibi bir Windows hizmeti oluşturma aracı ile bat dosyasını çalıştıracak bir hizmet ekleyebilirsiniz.
* Bat betiği, herhangi bir dizinden başlatıldığında bulunduğu dizini çalışma dizini olarak ayarlamaktadır. Bu yüzden, görev zamanlamasında veya hizmet ayarlarında, çalışma dizini olarak yazılımın bulunduğu dizin ayarlanmasa bile yazılım doğru şekilde çalışacaktır.
> NOT: Henüz bağlantı kopukluğu tespitinde bazı sorunlar bulunmaktadır ve uzun süreli çalışmalarda bazen kendiliğinden yeniden bağlanma özelliği çalışmamaktadır. Bu yüzden görev zamanlamasını veya hizmet ayarlarını, şimdilik görevin/hizmetin günde 1-2 kere yeniden başlatılacağı şekilde yapınız.

---

## Installation and Running:

### Requirements:
- Windows operating system.
- Python 3.x
- The following additional Python packages:
  - mysql-connector-python==8.2.0
  - Flask==3.0.0
  - Flask-Cors==4.0.0

Python packages can be installed via the requirements.txt file:
```
pip install -r requirements.txt
```

### Installation:
The software is portable, download and place it in an appropriate directory on the server.

### Running:
After configuring the necessary settings, run the start.bat script file. You can create a task schedule for automatic startup.
* The bat script is prepared to run directly as a service. You can add a service that will run the bat file using appropriate commands or a Windows service creation tool like Servy.
* The bat script sets its own directory as the working directory when started from any directory. Therefore, even if the software's directory is not set as the working directory in the task schedule or service settings, the software will work correctly.
> NOTE: There are still some issues with connection loss detection, and sometimes the automatic reconnection feature does not work during long-term operations. Therefore, for now, configure the task schedule or service settings so that the task/service is restarted 1-2 times a day.

---

## Ayarlamalar:

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
  - enabled = true veya false. ACARS ağı ARINC 622 uygulamalarının çözülmesi ile ilgili arka yazılım işlevlerinin etkinleştirilip etkinleştirilmeyeceğini belirler.

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

## Configuration:

### Data Link Infrastructure Setup:
For the software to work, a software that can demodulate and decode data link subnetwork signals and transmit ACARS network messages (ATN network is not currently supported) in appropriate JSON format via TCP server must be installed and running. Additionally, messages from multiple feeders can be collected in a single TCP server via intermediate software and then forwarded to the backend software.
* To collect data from multiple feeders with different protocols and transmit it to the backend software as a TCP server, you can use this software: [acars_router](https://github.com/sdr-enthusiasts/acars_router)
  * acars_router should be configured as "TCP server".

Some of the following software does not directly support TCP transmission, but can be used to provide data via acars_router or other relay software.

* For ACARS network decoding via VDL M0/A subnetwork: [acarsdec](https://github.com/f00b4r0/acarsdec)
* For ACARS network decoding via VDL M2 subnetwork: [vdlm2dec](https://github.com/TLeconte/vdlm2dec)
* For ACARS network decoding via HFDL subnetwork: [acarshfdl](https://github.com/szpajder/dumphfdl)
* For ACARS network decoding via INMARSAT Classic Aero subnetwork: [JAERO](https://github.com/jontio/JAERO)

Not yet supported but for ATN network:
* For ATN network decoding via VDL M2 subnetwork: [dumpvdl2](https://github.com/szpajder/dumpvdl2)


### Software Configuration:
A MySQL-based database server is required for records, and an empty database must be created in it. The required tables will be added to the database by the software.

Settings are made via the config.ini file. The explanations of the settings are as follows:

- [DATABASE]
  - host = IP address of MySQL-based database server (e.g., localhost)
  - port = Port number of database server (e.g., 3306)
  - user = Database username.
  - password = Database user password.
  - database = Name of the database to be used.
- [BACKEND]
  - host = IP address of the web server for frontend software to connect (e.g., localhost)
  - port = Port number of the web server for frontend software to connect (e.g., 10002)
- [LISTENER]
  - host = IP address of the TCP server that will send messages (e.g., localhost)
  - port = Port number of the TCP server that will send messages (e.g., 15551)
  - max_idle_time = Maximum idle time (in seconds) allowed for connection loss detection as a backup, apart from instant connection loss detection. If no new message is received after this time, the reconnection process is initiated. (e.g., 600)
- [RECORDING]
  - max_messages = Maximum number of messages to be stored in the database. When this number is reached, the oldest messages are deleted and new messages are recorded. (e.g., 100000)
- [LOGGING]
  - max_log_size_mb = Maximum size of the log file (in MB) (e.g., 10)
  - backup_count = Number of log file backups (e.g., 2)
- [DECODING]
  - enabled = true or false. Determines whether backend software functions related to decoding ACARS network ARINC 622 applications are enabled.

### Using Reverse Proxy:
If the frontend software will be published in an internet environment rather than a local network and you want to use a domain name instead of direct IP access when configuring the frontend software, you can use a Reverse Proxy. With appropriate software (IIS, Nginx, Apache, etc.) and configurations, you can redirect requests from outside with a specific domain name and/or subdomain to the server and port where the backend software is running. When configuring the Reverse Proxy, you must use software that supports SSE (Server-Sent Events) and ensure that SSE requests are properly redirected.

Example Nginx configuration:
```
server {
        listen xxx.xxx.xxx.xxx:2053 ssl;   // IP address and port that nginx will listen to
        server_name dlink-api.ibosoft.net.tr;    // Domain name to be used for frontend software access

        ssl_certificate     ssl/cert.pem;   // SSL certificate (optional)
        ssl_certificate_key ssl/key.pem;    // SSL certificate key (optional)

        location ~ ^/error_docs/.*\.htm$ {
            root ./;
            internal;
        }

        // (Optional) To make access from outside the website where you will publish the frontend software more difficult, you can add http_referer control with your own domain name and the domain name you use for backend software access. (e.g., atc.ibosoft.net.tr and dlink-api.ibosoft.net.tr:2053)

        if ($http_referer !~ "^https://(atc\.ibosoft\.net\.tr|dlink-api\.ibosoft\.net\.tr(:2053)?)/") {
            return 403;
        }

        // Required settings for SSE requests

        location / {
            proxy_pass http://127.0.0.1:10002;    // Server and port where the backend software is running ([BACKEND] settings), SSL termination is done with http://
            proxy_http_version 1.1;

            # Important SSE settings:
            proxy_set_header Connection '';
            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 6h;
            proxy_send_timeout 60s;
            tcp_nodelay on;

            # SSE headers
            add_header Cache-Control no-cache;
            add_header X-Accel-Buffering no;

            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
```

### Other Considerations:
* You can use Cloudflare proxy service along with Reverse Proxy. To benefit from the proxy service on Cloudflare's free plan, one of the supported ports must be used. For example, 443 (default https port), 2053, 2083, 2087, 2096, or 8443 ports can be used. Port 2053 is used in the Reverse Proxy example.

---

## Yazılımın İşleyişi Hakkında Detaylar:

### JSON Yapısı:
Yazılım, TCP ile getirilen ASCII kodlu iletilerden JSON verisini ayrıştırır. Beklenen JSON yapısı örneği aşağıdaki gibidir:

```json
{
  "freq": 131.725,
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
- `mode`: ACARS ileti modu (Subnetwork türü değildir. VDL M0/A, M2 vs. ile karıştırmayın.) (Uç yazılımda işlevsiz.)
- `label`: ACARS ileti Label'i
  > **NOT:** `_DEL` label'i (DEL ASCII DEL karakteridir, 0x7F) metin kodlama kısıtlamaları nedeniyle `_d` olarak gönderilmelidir.
- `block_id`: ACARS ileti Blok numarası
- `ack`: ACARS ileti ACK bayrağı (true/false)
- `tail`: ARINC 618/620 Aircraft Address (Uçak kuyruk numarası)
- `text`: ACARS ileti metin içeriği
- `msgno`: Downlink iletileri için ARINC 618/620 Downlink Sequence Number (Uç yazılımda işlevsiz.)
- `flight`: ARINC 618/620 Flight Identifier

### Veritabanı Yapısı:
Yazılım, veri tabanında `messages_json_raw` adında bir tablo oluşturur ve iletileri bu tabloya kaydeder. Tablo yapısı, JSON yapısı ile uyumlu olacak şekilde ayarlanmıştır ve aşağıdaki gibidir:

| Sütun Adı       | Tür         | Açıklama                                      |
|-----------------|-------------|-----------------------------------------------|
| id              | INT (Auto Increment) | Birincil anahtar                     |
| received_at     | TIMESTAMP   | İletinin alındığı zaman                       |
| source_ip       | VARCHAR(45) | İletinin kaynak IP adresi                     |
| source_port     | INT         | İletinin kaynak portu                         |
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
| msgno           | VARCHAR(20) | Downlink Sequence Number                      |
| flight          | VARCHAR(20) | Flight Identifier                             |
| assstat         | VARCHAR(50) | İlişkilendirme durumu                         |
| app_name        | VARCHAR(50) | Uygulama adı                                  |
| app_ver         | VARCHAR(50) | Uygulama sürümü                               |


### ARINC 620 ve ARINC 622 Uygulamalarının Çözülmesi:

* ACARS iletilerinin, ARINC 620 ve ICAO SARP'larına göre uygun uygulama (ACARS Application) türlerine göre sınıflandırılması, uç yazılım tarafından Ibosoft Acars Decoding Library ve uç yazılım içerisindeki bazı kodlar aracılığıyla yapılmaktadır.
* ARINC 620 dahilinde çözümlenmesi açıklanan iletilerin/uygulamalarının çözümlenmesi, uç yazılım tarafında Ibosoft Acars Decoding Library aracılığıyla yapılmaktadır.
* Uç yazılımın; ACARS ağı üzerinden işleyen ARINC 622 uygulamalarının (ADS-C, CPDLC, MIAM ve bazı "H1" Label'li mühendislik iletileri) çözebilmesi için hazır bir kütüphane kullanılmıştır, derlenmiş DLL dosyası doğrudan projeye dahil edilmiştir. Bakınız: [libacars](https://github.com/szpajder/libacars)
* libacars, "SA" Label'li (Media Advisory) iletileri de çözebilmektedir ancak bu Label'li iletilerin çözümlemesi, uç yazılım tarafında Ibosoft Acars Decoding Library ile yapılmaktadır.
* libacars kütüphanesinin yapısı gereği, kütüphanenin arka yazılıma dahil edilmesi kararı alınmıştır.
* ARINC 622 uygulamları çözülürken, canlı iletiler için, ileti ACARS ağı iletisi ise ve ileti Label'i AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1 ise ileti arka yazılımda çözülür ve canlı ileti bilgisiyle birlikte uç yazılıma iletilir.
* Geçmiş iletilerde, uç yazılım doğrudan PHP aracılığıyla veritabanına eriştiği için arka yazılımı doğrudan kullanmaz. ARINC 622 uygulamaları ise arka yazılım tarafında çözümlemesi yapıldığı için, arka yazılıma bir API eklenmiştir. Uç yazılım, geçmiş iletiler için ARINC 622 uygulamalarını çözmek istediğinde, arka yazılıma bir istek gönderir ve arka yazılım iletiyi çözüp sonucu uç yazılıma iletir. Bu işlev için, iletinin ACARS ağı iletisi ve ileti Label'inin AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1 olması gerekmektedir.


### Yeniden Bağlantı Denemesi:
Yazılım, TCP bağlantısı koptuğunda veya bağlantı kurulamadığında, kısa aralıklarla yeniden bağlanmayı dener. Yeniden bağlanma denemeleri sırasında, bağlantı kurulana kadar bekler ve bu sırada yeni iletiler alınamaz. Bağlantı kopukluğunun tespit edilememesi durumları için, ayarlarda belirtilen süre boyunca yeni bir ileti alınmazsa yeniden bağlanma işlemi başlatılır.

### Dosya Yapısı:
```
acars-backend/
├── main.py                 # Ana uygulama
├── database_handler.py     # Veritabanı işlemleri modülü
├── decode_handler.py       # ACARS ileti çözücü (libacars sarmalayıcı)
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

## Details About Software Operation:

### JSON Structure:
The software parses JSON data from ASCII-encoded messages received via TCP. An example of the expected JSON structure is as follows:

```json
{
  "freq": 131.725,
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

**Descriptions:**

- `freq`: Frequency (in MHz)
- `channel`: Channel number (non-functional in frontend software)
- `error`: Error status (0 = no error) (non-functional in frontend software)
- `level`: Signal level (in dBm)
- `timestamp`: Timestamp in the message (Unix epoch format) (Non-functional in frontend software.)
- `app`: Message generating application information
  - `name`: Application name (Frontend software determines Subnetwork and Network type according to application type. See frontend software guide for details.)
  - `ver`: Application version (Non-functional in frontend software.)
- `station_id`: Station identifier (In installations with different receivers, different station identifiers can be assigned to receivers.)
- `assstat`: Association status of blocks in multi-block ACARS messages (See frontend software guide.)
- `mode`: ACARS message mode (Not a Subnetwork type. Do not confuse with VDL M0/A, M2, etc.) (Non-functional in frontend software.)
- `label`: ACARS message Label
  > **NOTE:** The `_DEL` label (DEL is the ASCII DEL character, 0x7F) should be sent as `_d` due to text encoding limitations.
- `block_id`: ACARS message Block number
- `ack`: ACARS message ACK flag (true/false)
- `tail`: ARINC 618/620 Aircraft Address (Aircraft tail number)
- `text`: ACARS message text content
- `msgno`: ARINC 618/620 Downlink Sequence Number for downlink messages (Non-functional in frontend software.)
- `flight`: ARINC 618/620 Flight Identifier

### Database Structure:
The software creates a table named `messages_json_raw` in the database and records messages to this table. The table structure is configured to be compatible with the JSON structure and is as follows:

| Column Name     | Type        | Description                                   |
|-----------------|-------------|-----------------------------------------------|
| id              | INT (Auto Increment) | Primary key                          |
| received_at     | TIMESTAMP   | Time when the message was received            |
| source_ip       | VARCHAR(45) | Source IP address of the message              |
| source_port     | INT         | Source port of the message                    |
| timestamp_msg   | DOUBLE      | Timestamp in the message                      |
| station_id      | VARCHAR(50) | Station identifier                            |
| channel         | INT         | Channel number                                |
| freq            | DOUBLE      | Frequency                                     |
| level           | DOUBLE      | Signal level                                  |
| error           | INT         | Error status                                  |
| mode            | VARCHAR(10) | Mode                                          |
| label           | VARCHAR(20) | Label                                         |
| block_id        | VARCHAR(10) | Block identifier                              |
| ack             | BOOLEAN     | ACK flag                                      |
| tail            | VARCHAR(20) | Aircraft Address                              |
| text            | TEXT        | Message text content                          |
| msgno           | VARCHAR(20) | Downlink Sequence Number                      |
| flight          | VARCHAR(20) | Flight Identifier                             |
| assstat         | VARCHAR(50) | Association status                            |
| app_name        | VARCHAR(50) | Application name                              |
| app_ver         | VARCHAR(50) | Application version                           |


### Decoding ARINC 620 and ARINC 622 Applications:

* Classification of ACARS messages according to appropriate application (ACARS Application) types according to ARINC 620 and ICAO SARPs is done by the frontend software through Ibosoft Acars Decoding Library and some codes in the frontend software.
* Decoding of messages/applications that are described to be decoded within ARINC 620 is done by Ibosoft Acars Decoding Library on the frontend software side.
* For the frontend software to decode ARINC 622 applications (ADS-C, CPDLC, MIAM, and some "H1" labeled engineering messages) operating via ACARS network, a ready-made library has been used, and the compiled DLL file is directly included in the project. See: [libacars](https://github.com/szpajder/libacars)
* libacars can also decode "SA" labeled (Media Advisory) messages, but the decoding of these labeled messages is done by Ibosoft Acars Decoding Library on the frontend software side.
* Due to the structure of the libacars library, a decision was made to include the library in the backend software.
* When decoding ARINC 622 applications, for live messages, if the message is an ACARS network message and the message Label is AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1, the message is decoded in the backend software and forwarded to the frontend software along with live message information.
* For historical messages, the frontend software accesses the database directly via PHP, so it does not use the backend software directly. Since ARINC 622 applications are decoded on the backend software side, an API has been added to the backend software. When the frontend software wants to decode ARINC 622 applications for historical messages, it sends a request to the backend software, and the backend software decodes the message and forwards the result to the frontend software. For this function, the message must be an ACARS network message and the message Label must be AA (CPDLC), BA (CPDLC), A6 (ADS-C), B6 (ADS-C), MA (MIAM), H1.


### Reconnection Attempt:
When the TCP connection is lost or connection cannot be established, the software tries to reconnect at short intervals. During reconnection attempts, it waits until the connection is established, and new messages cannot be received during this time. For cases where connection loss cannot be detected, if no new message is received for the duration specified in the settings, the reconnection process is initiated.

### File Structure:
```
acars-backend/
├── main.py                 # Main application
├── database_handler.py     # Database operations module
├── decode_handler.py       # ACARS message decoder (libacars wrapper)
├── tcp_client.py           # TCP client module
├── sse_server.py           # SSE server module
├── config.ini              # Configuration file
├── requirements.txt        # Python dependencies
├── start.bat               # Windows startup script
├── LICENSE                 # License file
├── README.md               # This file
├── SSE_MIGRATION.md        # SSE migration documentation
├── libacars/               # libacars library folder
│   ├── libacars-2.dll      # libacars ARINC 622 decoder library
│   ├── zlib1.dll           # zlib compression library (dependency)
│   └── LICENSE.md          # libacars license file
└── atc_datalink.log        # Log file (Created when the software is run.)
```

---
