# CarScraping - Guida Installazione Unraid

## Panoramica
CarScraping è un tool avanzato per il monitoraggio di auto usate su AutoScout24.it con dashboard analytics in tempo reale. Questo documento fornisce una guida completa per l'installazione su Unraid.

## Installazione tramite Community Applications

### 1. Ricerca dell'App
1. Apri **Community Applications** in Unraid
2. Cerca **"CarScraping"**
3. Clicca su **Install** per avviare l'installazione

### 2. Configurazione Container

#### Porte di Rete
- **Web Interface**: 8787 (modificabile)
- **Database** (opzionale): 5432 per accesso esterno a PostgreSQL

#### Directory di Mapping
Configura i seguenti percorsi per la persistenza dei dati:

```
/mnt/user/appdata/carscraping/config → /config (configurazione app)
/mnt/user/appdata/carscraping/data   → /data (database PostgreSQL)
/mnt/user/appdata/carscraping/logs   → /logs (log applicazione)
```

#### Variabili d'Ambiente
- **SCRAPING_INTERVAL**: `24h` (frequenza scraping)
- **LOG_LEVEL**: `INFO` (livello logging)
- **DB_HOST**: `localhost` (host database)

### 3. Avvio e Verifica
1. Clicca **Apply** per creare il container
2. Attendi che il container sia in stato **Started**
3. Accedi alla web interface: `http://UNRAID-IP:8787`

## Configurazione Avanzata

### Setup Database Esterno
Se desideri utilizzare un database PostgreSQL esterno:

1. **Variabili d'ambiente aggiuntive**:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   DB_HOST=ip-database-esterno
   ```

2. **Disabilita container PostgreSQL interno**:
   - Rimuovi il mapping della porta 5432
   - Il container utilizzerà automaticamente il database esterno

### Configurazione Backup
Per backup automatici dei dati:

1. **Script Backup** (`/mnt/user/scripts/backup-carscraping.sh`):
   ```bash
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   BACKUP_DIR="/mnt/user/backups/carscraping"
   
   # Crea directory backup se non esiste
   mkdir -p "$BACKUP_DIR"
   
   # Backup configurazione
   tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" /mnt/user/appdata/carscraping/config
   
   # Backup database (se interno)
   docker exec CarScraping pg_dump -U carscraping carscraping > "$BACKUP_DIR/database_$DATE.sql"
   
   # Mantieni solo gli ultimi 7 backup
   find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
   find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
   ```

2. **Cron job** per esecuzione automatica:
   ```
   0 2 * * * /mnt/user/scripts/backup-carscraping.sh
   ```

### Ottimizzazione Performance

#### Resource Allocation
Per un utilizzo ottimale delle risorse:

- **CPU**: 2 core minimi, 4 raccomandati per scraping intensivo
- **RAM**: 2GB minimi, 4GB raccomandati
- **Storage**: SSD raccomandato per database

#### Network Configuration
Per reti isolate o VPN:

```yaml
# docker-compose override
networks:
  carscraping_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## Configurazione Ricerche

### Setup Iniziale
1. Accedi alla dashboard: `http://UNRAID-IP:8787`
2. Clicca **"Nuova Ricerca"** per configurare il primo scraping
3. Imposta filtri desiderati (marca, modello, prezzo, etc.)
4. Salva con nome identificativo

### Automazione Scraping
Il sistema esegue automaticamente scraping secondo l'intervallo configurato (`SCRAPING_INTERVAL`). Per modificare:

1. Ferma il container
2. Modifica la variabile `SCRAPING_INTERVAL`
3. Riavvia il container

Valori supportati:
- `6h` - Ogni 6 ore
- `12h` - Ogni 12 ore  
- `24h` - Giornaliero (default)
- `48h` - Ogni 2 giorni

## Monitoring e Logs

### Accesso Logs
I log sono accessibili in:
```
/mnt/user/appdata/carscraping/logs/
├── app.log          # Log applicazione principale
├── scraping.log     # Log operazioni scraping
└── error.log        # Log errori
```

### Health Check
Verifica stato applicazione:
```bash
curl http://UNRAID-IP:8787/health
```

Risposta attesa:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Metriche Performance
La dashboard include metriche real-time:
- Stato scraping in corso
- Performance database
- Utilizzo cache Redis
- Statistiche network request

## Troubleshooting

### Problemi Comuni

#### 1. Container non si avvia
**Causa**: Conflitto porte o directory non accessibili
**Soluzione**:
```bash
# Verifica porte in uso
netstat -tlnp | grep 8787

# Verifica permessi directory
ls -la /mnt/user/appdata/carscraping/
```

#### 2. Scraping fallisce
**Causa**: Rate limiting o blocco IP
**Soluzione**:
- Aumenta `request_delay` in configurazione
- Verifica log per errori HTTP
- Considera utilizzo VPN se necessario

#### 3. Database errori
**Causa**: PostgreSQL non accessibile
**Soluzione**:
```bash
# Test connessione database
docker exec CarScraping pg_isready -h localhost -U carscraping

# Reset database se corrotto
docker exec CarScraping psql -U carscraping -c "DROP DATABASE IF EXISTS carscraping; CREATE DATABASE carscraping;"
```

#### 4. Performance scadenti
**Causa**: Risorse insufficienti
**Soluzione**:
- Aumenta allocazione RAM
- Migra database su SSD
- Configura indici database

### Recovery Procedure

#### Ripristino da Backup
```bash
# Stop container
docker stop CarScraping

# Ripristina configurazione
cd /mnt/user/appdata/carscraping/
tar -xzf /mnt/user/backups/carscraping/config_YYYYMMDD_HHMMSS.tar.gz

# Ripristina database
docker start CarScraping
sleep 30  # Attendi avvio PostgreSQL
docker exec CarScraping psql -U carscraping < /mnt/user/backups/carscraping/database_YYYYMMDD_HHMMSS.sql
```

#### Factory Reset
Per reset completo dell'applicazione:
```bash
# Stop e rimuovi container
docker stop CarScraping
docker rm CarScraping

# Rimuovi dati (ATTENZIONE: perdita dati permanente)
rm -rf /mnt/user/appdata/carscraping/

# Reinstalla dall'Community Applications
```

## Sicurezza

### Accesso Web Interface
Per sicurezza aggiuntiva:

1. **Reverse Proxy** con nginx:
   ```nginx
   location /carscraping/ {
       proxy_pass http://localhost:8787/;
       proxy_set_header Host $host;
       proxy_set_header X-Real-IP $remote_addr;
   }
   ```

2. **VPN Access Only**:
   - Configura accesso solo tramite VPN Unraid
   - Blocca porta 8787 su firewall esterno

### Backup Encryption
Per backup sicuri:
```bash
# Backup criptato
tar -czf - /mnt/user/appdata/carscraping/ | gpg --cipher-algo AES256 --compress-algo 1 --symmetric --output carscraping_backup_$(date +%Y%m%d).tar.gz.gpg
```

## Supporto

### Risorse Utili
- **GitHub Repository**: https://github.com/batik95/CarScraping
- **Docker Hub**: https://hub.docker.com/r/batik95/carscraping
- **API Documentation**: `http://UNRAID-IP:8787/docs`

### Report Bug
Per segnalare problemi:
1. Raccoglia log rilevanti
2. Descrivi steps per riprodurre il problema
3. Apri issue su GitHub con dettagli completi

### Feature Request
Per richiedere nuove funzionalità:
1. Verifica che non sia già presente in roadmap
2. Descrivi use case specifico
3. Proponi implementazione se possibile