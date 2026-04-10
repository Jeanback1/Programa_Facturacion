# Sistema de Facturación

Aplicación de escritorio para gestión de facturación, construida con Python, CustomTkinter y SQLite.

## Stack

- **GUI**: CustomTkinter (tema oscuro)
- **Base de datos**: SQLite 3 (nativo)
- **Contraseñas**: bcrypt
- **Python**: 3.10+

## Instalación

```bash
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate.bat    # Windows
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Credenciales iniciales

| Usuario | Contraseña | Rol   |
|---------|------------|-------|
| admin   | admin123   | admin |

> Cambiar la contraseña del admin en el primer uso.

## Estructura

```
├── main.py                  # Punto de entrada
├── app/
│   ├── config.py            # Rutas y constantes globales
│   ├── session.py           # Singleton de sesión en memoria
│   ├── database/
│   │   ├── connection.py    # Singleton de conexión SQLite
│   │   └── migrations.py    # Creación de tablas y datos iniciales
│   ├── models/
│   │   └── usuario.py       # Dataclass Usuario
│   ├── repositories/
│   │   └── usuario_repo.py  # CRUD de usuarios
│   └── views/
│       ├── login_view.py    # Pantalla de login
│       └── home_view.py     # Pantalla principal
└── data/                    # Base de datos (excluida de git)
```

## Datos de la BD

- **Linux**: `~/.local/share/facturacion/data.db`
- **Windows**: `%LOCALAPPDATA%\Facturacion\data.db`
