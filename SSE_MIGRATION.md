# WebSocket'ten SSE'ye (Server-Sent Events) Geçiş

## Neden SSE?

WebSocket yerine SSE (Server-Sent Events) kullanmaya geçtik çünkü:

1. **Reverse Proxy Uyumluluğu**: SSE standart HTTP/HTTPS üzerinden çalışır, bu nedenle nginx, Apache gibi reverse proxy'lerle mükemmel uyumludur
2. **Tek Yönlü İletişim**: Zaten sadece server'dan client'a mesaj gönderiyorduk, SSE tam da bunun için tasarlanmış
3. **Otomatik Yeniden Bağlanma**: SSE, tarayıcı tarafında otomatik yeniden bağlanma desteği sunar
4. **Daha Basit**: WebSocket'e göre daha az karmaşık, daha kolay hata ayıklama

## Yapılan Değişiklikler

### Backend Değişiklikleri

1. **websocket_server.py** → **sse_server.py**
   - WebSocket yerine Flask tabanlı SSE sunucusu
   - `/stream` endpoint'i ile SSE bağlantıları
   - `/health` endpoint'i ile sunucu durumu kontrolü
   - Queue tabanlı mesaj dağıtımı
   - Otomatik heartbeat (15 saniyede bir)

2. **main.py**
   - `WebSocketServer` yerine `SSEServer` kullanımı
   - İlgili fonksiyon isimleri güncellendi

3. **requirements.txt**
   - `websockets` kaldırıldı
   - `Flask` ve `Flask-Cors` eklendi

### Frontend Değişiklikleri

**page-data-link.php**
- `WebSocket` yerine `EventSource` API kullanımı
- Daha basit bağlantı yönetimi
- Otomatik yeniden bağlanma mekanizması

## Kurulum

### Gerekli Paketleri Yükleyin

```powershell
cd d:\ibosoft\ATC\atc-datalink-backend
pip install -r requirements.txt
```

### Eski websocket_server.py'yi Kaldırın (Opsiyonel)

```powershell
# Yedek alın
Move-Item websocket_server.py websocket_server.py.backup

# veya tamamen silin
Remove-Item websocket_server.py
```

## Çalıştırma

Backend'i normal şekilde başlatın:

```powershell
python main.py
```

Veya:

```powershell
start.bat
```

## Nginx Reverse Proxy Yapılandırması

SSE için nginx yapılandırması:

```nginx
location /stream {
    proxy_pass http://127.0.0.1:10002/stream;
    proxy_http_version 1.1;
    proxy_set_header Connection '';
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # SSE için önemli ayarlar
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;
    chunked_transfer_encoding on;
}

location /health {
    proxy_pass http://127.0.0.1:10002/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Test

### Backend'i Test Edin

```powershell
# Health check
curl http://localhost:10002/health

# SSE stream'i test edin (PowerShell)
Invoke-WebRequest -Uri http://localhost:10002/stream -TimeoutSec 999
```

### Frontend'i Test Edin

Tarayıcınızda web sayfasını açın ve:
1. Bağlantı durumu "Connected" olmalı
2. Mesajlar gerçek zamanlı olarak gelmelidir
3. Sayfa yenilendiğinde geçmiş mesajlar yüklenmelidir

## Avantajlar

✅ HTTP/HTTPS reverse proxy ile tam uyumluluk
✅ SSL/TLS sertifikası yönetimi daha kolay
✅ Standart HTTP portu (443) kullanılabilir
✅ Firewall ve güvenlik duvarlarıyla daha az sorun
✅ Tarayıcı konsolu ve ağ araçlarıyla daha kolay hata ayıklama
✅ Otomatik yeniden bağlanma tarayıcı tarafından yönetilir

## Port Bilgileri

- Backend SSE Sunucusu: `127.0.0.1:10002`
- UDP Listener: `192.168.100.101:15551`
- Frontend Erişim: `https://dlink-api.ibosoft.net.tr:2053/stream`

## Notlar

- SSE bağlantıları tek yönlüdür (sadece server → client)
- Her 15 saniyede bir heartbeat gönderilir (bağlantıyı canlı tutar)
- Maksimum 100 mesaj queue'sü per client
- Queue dolduğunda client otomatik disconnect edilir
- CORS tüm origin'ler için etkinleştirilmiştir
