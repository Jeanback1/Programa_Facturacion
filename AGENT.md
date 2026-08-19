# AGENT.md

Guía para agentes de IA que trabajan con este repositorio.

Este proyecto es un sistema de facturación de escritorio (CustomTkinter + SQLite)
para un local de comida. App en español, impresión de tickets térmicos ESC/POS.

## Cómo ejecutar

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Credenciales por defecto: `admin` / `admin123`

En Windows se distribuye como ejecutable compilado con PyInstaller (`main.spec`).
Ver `feat` de impresión: python-escpos 3.x necesita definir la variable
`ESCPOS_CAPABILITIES_FILE` en builds congelados (ya resuelto en
`app/printing/impresora.py` → `_asegurar_capabilities()`).

## Arquitectura

App de escritorio por capas:

```
config.py / session.py
    ↓
app/database/   (connection singleton, migrations)
    ↓
app/models/     (dataclasses)
    ↓
app/repositories/  (todo el SQL — nunca llamar a BD desde views)
    ↓
app/views/      (frames CTk)
    ↓
main.py         (ventana raíz del App, controlador de navegación)
```

### Navegación

`App.navigate(destino: str)` en `main.py` es el único punto de entrada de
navegación. Destruye el frame actual e instancia la vista nueva. Cada vista
recibe `(master, navigate)` en su constructor. Rutas: `"login"` → `"home"`
→ `"facturar"`. También `"gestion"` (productos) y `"cuadre"`.

Para añadir una pantalla: crear `app/views/nueva_view.py` con una clase que
herede de `ctk.CTkFrame`, añadir una rama en `App.navigate()`, y llamar a
`self._navigate("nueva")` desde cualquier vista.

### Vistas

Todas heredan de `ctk.CTkFrame` con este patrón:

```python
class NuevaView(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master)
        self._navigate = navigate
        self.pack(fill="both", expand=True)
        self._construir_ui()
```

Cada vista configura tamaño de ventana con `master.geometry(...)` y
`master.resizable(...)` en `_construir_ui()`.

### Estado compartido

- `Session()` — singleton con el `Usuario` autenticado. Acceso:
  `Session().usuario_actual`, `Session().es_admin()`.
- `_DatabaseConnection()` — conexión SQLite singleton. Nunca instanciar
  directamente desde vistas; usar repos.

### Patrón de repositorio

Todo el acceso a BD pasa por `app/repositories/`. Las funciones no reciben
objetos ORM; consultan con `get_connection()` y devuelven dataclasses de
`app/models/`. Ej: `usuario_repo.buscar_por_username(username) -> Optional[Usuario]`.

### Base de datos

SQLite. Ubicación:
- Linux: `~/.local/share/facturacion/data.db`
- Windows: `%LOCALAPPDATA%\Facturacion\data.db`

Las migraciones corren solas al arrancar vía `run_migrations()` en
`app/database/migrations.py`. Añadir tablas/columnas ahí con
`CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ... ADD COLUMN`.

### Variantes de producto (importante)

Los productos pueden tener hasta DOS grupos de variantes, en cascada:

- **Grupo 1 — "¿Qué guarnición?"** (`grupo=1`): solo modifica el nombre del
  producto. Sin efecto en precio. Ej: Arroz, Moro, Ensalada.
- **Grupo 2 — "Comer aquí o llevar"** (`grupo=2`): nombre + precio propio que
  REEMPLAZA el precio base del producto. Ej: Para llevar $480, Para comer $550.

La clave del item en la factura es compuesta:
`(producto_id, guarnicion_id, comer_llevar_id)` (los ids son `None` si ese
grupo no se eligió o no existe). El nombre final es concatenado:
`Hamburguesa (Arroz) (Para llevar)`.

Flujo: botón "Elegir opción" → popup guarnición (si hay) → popup comer/llevar
(si hay) → se agrega el item.

## Grafo de código (codebase-memory)

Este repositorio se indexa como **grafo de conocimiento** mediante el MCP
`codebase-memory`. El grafo permite moverse por el código por estructura y
relaciones (llamadas, herencia, data-flow), no solo por texto.

> IMPORTANTE: el grafo NO viaja en el repo (no hay `.codebase-memory/`
> versionado). Vive en el entorno del agente que lo indexa y se **reconstruye
> desde el código fuente**. Si el agente que abre este proyecto no ve el grafo,
> debe reconstruirlo con `index_repository`.

### Cómo indexar

```
index_repository(repo_path="<ruta/local/al/proyecto>", mode="full|moderate|fast")
```

- `full`: todos los archivos + aristas de similitud/semántica (máxima profundidad).
- `moderate`: archivos filtrados + similitud/semántica.
- `fast`: archivos filtrados, sin similitud/semántica (rápido, para tras cambios).
- `persistence=True`: escribe `.codebase-memory/graph.db.zst` en el repo para
  que otros entornos del MISMO tool puedan hacer bootstrap (evita re-indexar).

El nombre del proyecto derivado es `root-Programa_Facturacion` (o el que se
pase con `name=`).

### Cómo consultar (una vez indexado)

- `get_architecture(project, aspects)` — vista general: capas, hotspots,
  clusters, dependencias, entry points.
- `search_graph(query)` — búsqueda por lenguaje natural / nombre de símbolos.
- `search_code(pattern, project)` — grep enriquecido con el grafo.
- `get_code_snippet(qualified_name, project)` — lee el código de un símbolo.
- `trace_path(function_name, project, mode="calls|data_flow|cross_service")` —
  sigue llamadas / flujo de datos / llamadas entre servicios.
- `query_graph(cypher, project)` — consulta Cypher libre (multi-hop, agregaciones).
- `get_graph_schema(project)` — nodos y aristas del grafo.

El `qualified_name` tiene forma `root-Programa_Facturacion.<módulo>.<símbolo>`,
ej: `root-Programa_Facturacion.app.views.facturar_view.FacturarView._agregar_a_factura`.

### Recomendación de flujo para un agente

1. Si el proyecto no está indexado o dudas de su vigencia, indexar con
   `index_repository` (usar `full` para explorar bien, `fast` tras cambios).
2. Para entender una feature: `get_architecture` primero, luego `trace_path`
   sobre el punto de entrada o una función clave.
3. Antes de editar: `get_code_snippet` del símbolo exacto y `trace_path`
   (inbound) para ver quién lo llama / qué romperías.
4. Tras modificar código: reindexar (`fast`) para mantener el grafo al día.

### Notas

- No hay tests ni linter configurados todavía.
- Los textos de la UI y el catálogo son en español; respetar ese idioma en
  strings de usuario y en nombres de negocio (p. ej. "comer aquí", "guarnición").
