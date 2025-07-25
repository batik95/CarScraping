# CarScraping - Guida Installazione Unraid Completa

## 📋 Panoramica

CarScraping è un tool avanzato per il monitoraggio automatico di auto usate su AutoScout24.it con dashboard analytics in tempo reale. Questa versione Unraid include tutto il necessario in un singolo container per un'installazione semplice e senza dipendenze.

### 🚀 Caratteristiche Container All-in-One
- **PostgreSQL integrato** - Database embedded per zero configurazione
- **Redis integrato** - Cache integrata per performance ottimali  
- **Supervisord** - Gestione multi-processo affidabile
- **Inizializzazione automatica** - Database e configurazione auto-setup
- **Health checks** - Monitoring continuo dello stato applicazione
- **Backup integrato** - Procedure di backup e recovery

## 🛠️ Installazione Step-by-Step

### Metodo 1: Community Applications (Raccomandato)

1. **Apri Community Applications**
   - Dal dashboard Unraid, clicca su "Apps"
   - Cerca **"CarScraping"**
   - Clicca su **"Install"**

2. **Configurazione Container**
   ```
   Container Name: CarScraping
   Repository: batik95/carscraping:unraid
   ```

3. **Porte di Rete**
   ```
   Web Interface: 8787 → 8787 (modificabile)
   Database (opzionale): 5432 → 5432 
   Redis (opzionale): 6379 → 6379
   ```

4. **Directory Mapping**
   ```
   /mnt/user/appdata/carscraping/config → /config
   /mnt/user/appdata/carscraping/data   → /data  
   /mnt/user/appdata/carscraping/logs   → /logs
   ```

5. **Variabili d'Ambiente Base**
   ```
   SCRAPING_INTERVAL: 24 (ore)
   LOG_LEVEL: INFO
   DEBUG: false
   ```

6. **Avvia Container**
   - Clicca **"Apply"**
   - Attendi che lo stato diventi **"Started"**
   - Il primo avvio richiede 2-3 minuti per l'inizializzazione

### Metodo 2: Template Manual Import

1. **Download Template**
   ```bash
   wget https://raw.githubusercontent.com/batik95/CarScraping/main/unraid/CarScraping.xml
   ```

2. **Import in Unraid**
   - Docker → Add Container → Template: "user templates"
   - Incolla contenuto XML o carica file
   - Configura secondo necessità

## ⚙️ Configurazione Avanzata

### Personalizzazione Scraping

#### Intervallo Scraping
```
SCRAPING_INTERVAL: 6   # Ogni 6 ore
SCRAPING_INTERVAL: 12  # Ogni 12 ore  
SCRAPING_INTERVAL: 24  # Giornaliero (default)
SCRAPING_INTERVAL: 48  # Ogni 2 giorni
```

#### Performance Tuning
```
MAX_RETRIES: 3         # Retry scraping fallito
REQUEST_DELAY: 1.0     # Delay tra richieste (secondi)
DEBUG: true           # Debug mode per troubleshooting
```

### Database Esterno (Opzionale)

Per utilizzare PostgreSQL esterno invece di quello embedded:

1. **Prepara Database Esterno**
   ```sql
   CREATE USER carscraping WITH PASSWORD 'your_password';
   CREATE DATABASE carscraping OWNER carscraping;
   GRANT ALL PRIVILEGES ON DATABASE carscraping TO carscraping;
   ```

2. **Configura Variabile**
   ```
   DATABASE_URL: postgresql://carscraping:your_password@your_db_host:5432/carscraping
   ```

3. **Rimuovi Mapping Volume Database**
   - Non mappare `/data` se utilizzi database esterno
   - Il container utilizzerà automaticamente l'URL fornito

### Configurazione Backup Automatico

#### Script Backup (`/mnt/user/scripts/backup-carscraping.sh`)
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/mnt/user/backups/carscraping"
DATA_DIR="/mnt/user/appdata/carscraping"

# Crea directory backup
mkdir -p "$BACKUP_DIR"

# Backup configurazione
echo "Backup configurazione..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" "$DATA_DIR/config"

# Backup database (se embedded)
echo "Backup database..."
if [ -d "$DATA_DIR/data/postgres" ]; then
    docker exec CarScraping pg_dump -U carscraping carscraping > "$BACKUP_DIR/database_$DATE.sql"
fi

# Backup logs recenti
echo "Backup logs..."
find "$DATA_DIR/logs" -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" {} +

# Cleanup vecchi backup (mantieni 30 giorni)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.sql" -mtime +30 -delete

echo "Backup completato: $BACKUP_DIR"
```

#### Automazione con Cron
```bash
# Aggiunge a User Scripts plugin
# Frequenza: Daily at 2:00 AM
0 2 * * * /mnt/user/scripts/backup-carscraping.sh >/dev/null 2>&1
```

## 🎯 Utilizzo e Configurazione Applicazione

### Primo Accesso

1. **Accedi alla Dashboard**
   ```
   URL: http://UNRAID-IP:8787
   ```

2. **Crea Prima Ricerca**
   - Clicca **"Nuova Ricerca"**
   - Configura filtri auto desiderata:
     - Marca e modello
     - Range prezzo
     - Chilometraggio
     - Anno produzione
     - Alimentazione
   - Assegna nome identificativo
   - Salva ricerca

3. **Avvia Scraping Manuale**
   - Seleziona ricerca creata
   - Clicca **"Esegui Scraping"**
   - Monitora progress in tempo reale

### Dashboard Analytics

#### KPI Principali
- **Prezzo Medio**: Calcolato su tutte le auto trovate
- **Range Prezzi**: Min/Max con distribuzione
- **Numero Annunci**: Totale auto monitorate
- **Trend Prezzi**: Grafici storici per tracking nel tempo

#### Filtri Avanzati
- **Geografici**: Per provincia/regione
- **Tecnici**: Alimentazione, cambio, carrozzeria
- **Performance**: Potenza, cilindrata
- **Condizioni**: Anno, chilometraggio

### Automazione Scraping

#### Configurazione Scheduler
Il sistema esegue automaticamente scraping secondo `SCRAPING_INTERVAL`:

```bash
# Modifica intervallo (richiede restart container)
docker stop CarScraping
docker start CarScraping
```

#### Monitoraggio Logs
```bash
# Logs applicazione
tail -f /mnt/user/appdata/carscraping/logs/app.log

# Logs scraping
tail -f /mnt/user/appdata/carscraping/logs/scraping.log

# Logs database  
tail -f /mnt/user/appdata/carscraping/logs/postgresql.log
```

## 🔧 Troubleshooting

### Problemi Comuni

#### Container non si avvia
**Sintomi**: Container stato "stopped" o "error"

**Diagnosi**:
```bash
# Verifica logs container
docker logs CarScraping

# Verifica porte in uso
netstat -tlnp | grep -E "8787|5432"

# Verifica permessi directory
ls -la /mnt/user/appdata/carscraping/
```

**Soluzione**:
```bash
# Fix permessi
chown -R 99:100 /mnt/user/appdata/carscraping/

# Libera porte se occupate
fuser -k 8787/tcp

# Restart container
docker restart CarScraping
```

#### Database non si inizializza
**Sintomi**: Errori database connection nella dashboard

**Diagnosi**:
```bash
# Verifica logs PostgreSQL
tail -100 /mnt/user/appdata/carscraping/logs/postgresql.log

# Test connessione database
docker exec CarScraping pg_isready -h localhost -U carscraping
```

**Soluzione**:
```bash
# Reset database (ATTENZIONE: perdita dati)
docker stop CarScraping
rm -rf /mnt/user/appdata/carscraping/data/postgres
docker start CarScraping

# Il database verrà ricreato automaticamente
```

#### Scraping fallisce continuamente
**Sintomi**: Nessuna auto trovata, errori HTTP nei logs

**Diagnosi**:
```bash
# Verifica logs scraping dettagliati
grep "ERROR\|WARNING" /mnt/user/appdata/carscraping/logs/scraping.log

# Test connettività
docker exec CarScraping curl -I https://www.autoscout24.it
```

**Soluzioni**:
1. **Rate Limiting**: Aumenta `REQUEST_DELAY` a 2-3 secondi
2. **IP Blocked**: Configura VPN o proxy
3. **User-Agent**: Il sistema ruota automaticamente UA
4. **Network**: Verifica connessione internet Unraid

#### Performance Scadenti
**Sintomi**: Dashboard lenta, scraping molto lento

**Ottimizzazioni**:
```bash
# Alloca più RAM al container
# Docker → Edit → Advanced View → Extra Parameters:
--memory=2g --cpus=2

# Ottimizza database
docker exec CarScraping psql -U carscraping -c "VACUUM ANALYZE;"

# Pulisci logs vecchi
find /mnt/user/appdata/carscraping/logs -name "*.log" -mtime +30 -delete
```

### Recovery e Backup

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

#### Factory Reset Completo
```bash
# ATTENZIONE: Perdita dati permanente!

# Stop e rimuovi container
docker stop CarScraping
docker rm CarScraping

# Rimuovi tutti i dati
rm -rf /mnt/user/appdata/carscraping/

# Reinstalla da Community Applications
# I dati verranno ricreati da zero
```

### Log Monitoring

#### Script Monitoring Automatico
```bash
#!/bin/bash
# /mnt/user/scripts/monitor-carscraping.sh

LOG_FILE="/mnt/user/appdata/carscraping/logs/app.log"
ALERT_EMAIL="your-email@domain.com"

# Controlla errori critici
if grep -q "CRITICAL\|FATAL" "$LOG_FILE"; then
    echo "ALERT: CarScraping critical errors detected" | mail -s "CarScraping Alert" "$ALERT_EMAIL"
fi

# Controlla spazio disco
DISK_USAGE=$(df /mnt/user/appdata/carscraping/ | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "ALERT: CarScraping disk usage at ${DISK_USAGE}%" | mail -s "CarScraping Disk Alert" "$ALERT_EMAIL"
fi

# Verifica health check
if ! curl -f http://localhost:8787/health >/dev/null 2>&1; then
    echo "ALERT: CarScraping health check failed" | mail -s "CarScraping Health Alert" "$ALERT_EMAIL"
fi
```

## 🔒 Sicurezza e Best Practices

### Accesso Sicuro

#### Reverse Proxy con nginx
```nginx
# /mnt/user/appdata/nginx/nginx.conf
server {
    listen 443 ssl;
    server_name carscraping.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8787;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### VPN-Only Access
```bash
# Blocca accesso esterno (solo VPN)
iptables -I INPUT -p tcp --dport 8787 ! -s 10.0.0.0/8 -j DROP
iptables -I INPUT -p tcp --dport 8787 ! -s 192.168.0.0/16 -j DROP
```

### Backup Encryption
```bash
# Backup criptato con GPG
tar -czf - /mnt/user/appdata/carscraping/ | \
gpg --cipher-algo AES256 --compress-algo 1 --symmetric \
--output carscraping_backup_$(date +%Y%m%d).tar.gz.gpg
```

## 📊 Monitoring e Metriche

### Health Check Endpoints
```bash
# Status applicazione
curl http://localhost:8787/health

# Statistiche database
curl http://localhost:8787/api/stats/database

# Performance scraping
curl http://localhost:8787/api/stats/scraping
```

### Grafana Integration (Opzionale)
Se hai Grafana configurato, puoi monitorare CarScraping:

```json
{
  "dashboard": {
    "title": "CarScraping Monitoring",
    "panels": [
      {
        "title": "Scraping Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "carscraping_scraping_success_rate"
          }
        ]
      }
    ]
  }
}
```

## 🆘 Supporto e Risorse

### Documentazione
- **Repository**: https://github.com/batik95/CarScraping
- **Docker Hub**: https://hub.docker.com/r/batik95/carscraping
- **API Docs**: `http://your-unraid-ip:8787/docs`

### Community Support
- **GitHub Issues**: Per bug reports e feature requests
- **Unraid Forums**: Thread dedicato nella sezione Docker
- **Discord**: Community server per supporto real-time

### Bug Report Template
Quando segnali un problema, includi:

1. **Versione Unraid**: `cat /etc/unraid-version`
2. **Container Logs**: `docker logs CarScraping`
3. **System Info**: CPU, RAM, disk space
4. **Configuration**: Variabili environment utilizzate
5. **Steps to Reproduce**: Passaggi dettagliati per riprodurre
6. **Expected vs Actual**: Comportamento atteso vs osservato

### Feature Requests
Per nuove funzionalità:
1. Verifica roadmap esistente
2. Descrivi use case specifico  
3. Proponi implementazione se possibile
4. Considera backward compatibility

---

## 📋 Checklist Post-Installazione

- [ ] Container in stato "Started"
- [ ] Web interface accessibile su porta 8787
- [ ] Health check endpoint risponde: `/health`
- [ ] Directory mapping corretti e permessi OK
- [ ] Prima ricerca creata e salvata
- [ ] Scraping manuale testato con successo
- [ ] Logs accessibili e senza errori critici
- [ ] Backup script configurato e testato
- [ ] Monitoring configurato (opzionale)
- [ ] Accesso sicuro configurato (opzionale)

Con questa guida completa dovresti essere in grado di installare, configurare e utilizzare CarScraping su Unraid senza problemi. Per assistenza aggiuntiva, utilizza i canali di supporto indicati sopra.