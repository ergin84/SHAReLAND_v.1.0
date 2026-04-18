# pgAdmin Configuration

pgAdmin è stato configurato per gestire il database PostgreSQL di ShareLand.

## Accesso

- **URL**: http://localhost:5050
- **Email**: admin@shareland.it
- **Password**: admin

## Configurazione Server PostgreSQL

Dopo il primo accesso, aggiungi il server PostgreSQL seguendo questi passaggi:

1. Clicca su **"Add New Server"** (o "Aggiungi Nuovo Server")
2. Nella tab **"General"**:
   - **Name**: `ShareLand PostgreSQL` (o qualsiasi nome)
3. Nella tab **"Connection"**:
   - **Host name/address**: `db` (nome del servizio Docker)
   - **Port**: `5432`
   - **Maintenance database**: `Open_Landscapes`
   - **Username**: `postgres`
   - **Password**: `admin`
   - ✅ Spunta **"Save password"** per salvare la password
4. Clicca su **"Save"**

## Note

- Il nome host `db` funziona perché pgAdmin e PostgreSQL sono nella stessa rete Docker
- Se accedi da fuori Docker, usa `localhost` come host e porta `5433`











