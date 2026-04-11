# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Application

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Default credentials: `admin` / `admin123`

## No Tests or Linter Configured

There are no test files or lint configuration in this project. Tests and a linter have not been set up yet.

## Architecture

The app is a CustomTkinter desktop billing system using a layered architecture:

```
config.py / session.py
    ↓
app/database/   (connection singleton, migrations)
    ↓
app/models/     (dataclasses)
    ↓
app/repositories/  (all SQL — never call DB from views)
    ↓
app/views/      (CustomTkinter frames)
    ↓
main.py         (App root window, navigation controller)
```

### Navigation

`App.navigate(destino: str)` in `main.py` is the single navigation entry point. It destroys the current frame and instantiates the new view. Every view receives `(master, navigate)` in its constructor. Current routes: `"login"` → `"home"` → `"facturar"`.

To add a new screen: create `app/views/nueva_view.py` with a class subclassing `ctk.CTkFrame`, add a branch in `App.navigate()`, and call `self._navigate("nueva")` from any view.

### Views

All views subclass `ctk.CTkFrame` and follow this pattern:

```python
class NuevaView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master)
        self._navigate = navigate
        self.pack(fill="both", expand=True)
        self._construir_ui()
```

Each view configures the window size via `master.geometry(...)` and `master.resizable(...)` in `_construir_ui()`.

### Shared State

- `Session()` — singleton holding the authenticated `Usuario` in memory. Access `Session().usuario_actual`, `Session().es_admin()`.
- `_DatabaseConnection()` — singleton SQLite connection. Never instantiate directly from views; use repositories.

### Repository Pattern

All database access goes through `app/repositories/`. Functions receive no ORM objects — they query via `get_connection()` and return model dataclasses. Example: `usuario_repo.buscar_por_username(username) -> Optional[Usuario]`.

### Database

SQLite. Location:
- Linux: `~/.local/share/facturacion/data.db`
- Windows: `%LOCALAPPDATA%\Facturacion\data.db`

Schema migrations run automatically on startup via `run_migrations()` in `main.py`. Add new tables/columns there using `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`.

### Current Status

Phase 1 is complete (auth + home screen). `FacturarView` is scaffolded but all action methods (`buscar_producto`, `agregar_producto`, `imprimir_factura`, `eliminar_producto`) are placeholders. The `"Cuadre"` and `"Gestión"` routes from `HomeView` are not yet implemented.
