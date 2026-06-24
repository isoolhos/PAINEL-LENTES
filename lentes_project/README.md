# Lentes Ops

Painel operacional em Django para acompanhamento do fluxo de lentes oftalmológicas com dados do Oracle/Tasy e rastreabilidade local.

## Como rodar em desenvolvimento

```powershell
cd lentes_project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Acesse `http://127.0.0.1:8000/lentes/`.

## Banco local

Por padrão o projeto usa SQLite em desenvolvimento. Para PostgreSQL, configure `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT`.

## Oracle/Tasy

A integração Oracle fica isolada em `integrations/oracle`.

Configure:

```env
ORACLE_ENABLED=True
ORACLE_CLIENT_LIB_DIR=C:\oracle\instantclient_19_27
ORACLE_USER=usuario
ORACLE_PASSWORD=senha
ORACLE_HOST=host
ORACLE_PORT=1521
ORACLE_SERVICE_NAME=service
```

O status exibido no painel é sempre calculado em Python pelo motor em `core/services/status_engine.py`. O campo local `status_atual` é apenas cache operacional para auditoria e performance.
