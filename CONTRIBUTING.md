# CONTRIBUTING

## Getting Started

```shell
sudo apt install python3-venv

# Markdown linter
sudo apt update && sudo apt install nodejs npm
sudo npm install -g markdownlint-cli

# Clone project
cd /path/to/projects
git clone ...

. .venv/bin/activate

pip install -e

# or including also dev dependencies
pip install -e ".[dev]"
```

## Project Organization

```
app/
 ├── main.py
 ├── api/
 │    ├── auth.py
 │    ├── purchases.py
 │    ├── wallet.py
 │    └── admin.py
 ├── services/
 │    ├── cashback_engine.py
 │    ├── wallet_service.py
 │    └── purchase_service.py
 ├── models/
 ├── schemas/
 ├── repositories/
 ├── core/
 │    ├── security.py
 │    ├── config.py
 │    └── logging.py
 └── tests/
```

Layering:

Controller → Service → Repository → DB

Business logic lives in services.
Repositories are thin.
