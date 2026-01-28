# ACARS Backend
08.01.2026

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

---



# ATC Datalink Backend

A Python backend system that listens to UDP messages containing ACARS data and stores them in a MySQL database. Designed to run on Windows servers.

## Features

- **UDP Message Listener**: Continuously listens for incoming UDP messages on a configurable IP and port
- **JSON Data Extraction**: Extracts and parses JSON data from ASCII-encoded UDP messages
- **MySQL Database Storage**: Automatically stores messages in a MySQL database with automatic table creation
- **Message Limit Management**: Automatically removes old messages when the configured limit is reached
- **Configurable Settings**: All settings managed through a simple INI configuration file
- **Logging**: Comprehensive logging to both file and console
- **Graceful Shutdown**: Handles system signals for proper cleanup

## Requirements

- Python 3.8 or higher
- MySQL Server 5.7 or higher
- Windows Server (or Windows 10/11)

## Installation

### 1. Install Python Dependencies

```powershell
pip install -r requirements.txt
```

### 2. Configure MySQL Database

Make sure you have MySQL Server installed and running. Note the following:
- Database host and port
- Database username and password
- The application will automatically create the database and tables if they don't exist

### 3. Configure the Application

Edit the `config.ini` file with your settings:

```ini
[DATABASE]
# MySQL Database configuration
host = localhost
port = 3306
user = root
password = your_password_here
database = atc_datalink

[BACKEND]
# Backend connection settings for frontend
host = 192.168.100.101
port = 10002

[LISTENER]
# UDP listener settings
host = 192.168.100.101
port = 15551

[RECORDING]
# Maximum number of messages to keep in messages_json_raw table
max_messages = 10000
```

#### Configuration Parameters

**DATABASE Section:**
- `host`: MySQL server IP address (default: localhost)
- `port`: MySQL server port (default: 3306)
- `user`: MySQL username
- `password`: MySQL password
- `database`: Database name to use

**BACKEND Section:**
- `host`: IP address for frontend connection (e.g., 192.168.100.101)
- `port`: Port for frontend communication (e.g., 10002)

**LISTENER Section:**
- `host`: IP address to bind the UDP listener to (e.g., 192.168.100.101)
- `port`: UDP port to listen on (e.g., 15551)

**RECORDING Section:**
- `max_messages`: Maximum number of messages to keep in the database. When this limit is reached, oldest messages are automatically deleted.

## Usage

### Running the Application

Start the backend server:

```powershell
python main.py
```

The application will:
1. Load configuration from `config.ini`
2. Connect to MySQL database (create database if needed)
3. Create the `messages_json_raw` table if it doesn't exist
4. Start listening for UDP messages on the configured IP and port
5. Process incoming messages and store them in the database

### Stopping the Application

Press `Ctrl+C` to gracefully stop the application.

## Database Schema

The application creates a table named `messages_json_raw` with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | INT (Auto Increment) | Primary key |
| received_at | TIMESTAMP | When the message was received |
| source_ip | VARCHAR(45) | Source IP address of the UDP message |
| source_port | INT | Source port of the UDP message |
| timestamp_msg | DOUBLE | Message timestamp |
| station_id | VARCHAR(50) | Station ID |
| channel | INT | Channel number |
| freq | DOUBLE | Frequency in MHz |
| level | DOUBLE | Signal level |
| error | INT | Error count |
| mode | VARCHAR(10) | Mode (e.g., "2") |
| label | VARCHAR(20) | Message label |
| block_id | VARCHAR(10) | Block ID |
| ack | BOOLEAN | Acknowledgement flag |
| tail | VARCHAR(20) | Aircraft tail number |
| text | TEXT | Message text content |
| msgno | VARCHAR(20) | Message number |
| flight | VARCHAR(20) | Flight number |
| assstat | VARCHAR(50) | Association status |
| app_name | VARCHAR(50) | Application name (acarsdec, vdlm2dec) |
| app_ver | VARCHAR(50) | Application version |

The table includes indexes on `received_at`, `station_id`, `freq`, `tail`, `flight`, and `app_name` for improved query performance.

### Database Migration

If you're upgrading from an older version with a different table structure, run the migration script:

```powershell
python migrate_database.py
```

**WARNING:** This will delete all existing data in the table!

## Message Format

The system expects UDP messages containing JSON data in the following format:

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
  "tail": "TC-SOA",
  "text": "SXS8U,0214,00039,0000, 55,0226,N 37.078,E 30.527,",
  "msgno": "M37A",
  "flight": "XQ008U"
}
```

**Note:** Proxied fields (`proxied`, `proxied_by`, `acars_router_version`, `acars_router_uuid`) are ignored and not stored in the database.

## Logging

The application logs to two destinations:
- **Console**: Real-time status messages
- **File**: `atc_datalink.log` - Detailed log file in the application directory

Log levels:
- INFO: General operational messages
- WARNING: Non-critical issues
- ERROR: Critical errors that may affect functionality
- DEBUG: Detailed debugging information

## Troubleshooting

### Cannot Connect to Database
- Verify MySQL server is running
- Check database credentials in `config.ini`
- Ensure the MySQL user has necessary permissions (CREATE DATABASE, CREATE TABLE, INSERT, DELETE)

### UDP Messages Not Received
- Verify the IP address and port in `config.ini` match your network configuration
- Check Windows Firewall settings to ensure the port is open
- Use `netstat -an | findstr :15551` to verify the port is listening

### Permission Denied on Port Binding
- Ensure no other application is using the same port
- On some systems, binding to specific IP addresses may require administrator privileges

## Project Structure

```
atc-datalink-backend/
├── main.py                 # Main application entry point
├── database_handler.py     # Database operations module
├── udp_listener.py         # UDP listener module
├── config.ini             # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── atc_datalink.log      # Log file (created at runtime)
```

## Future Enhancements

- Frontend integration for live message broadcasting (WebSocket support)
- REST API for querying stored messages
- Message filtering and alerting
- Statistical dashboards

## License

[Your License Here]

## Contact

[Your Contact Information]
