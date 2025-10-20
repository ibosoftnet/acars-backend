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
