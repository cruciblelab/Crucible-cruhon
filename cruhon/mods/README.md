# Cruhon Mod System

Cruhon'un mod sistemi Minecraft'tan ilham alır.
Bir mod core'u bile değiştirebilir.

---

## Mod Yapısı

```
mods/
└── my-mod/
    ├── mod.json       ← zorunlu
    └── __init__.py    ← zorunlu, register(api) içermeli
```

---

## mod.json

```json
{
    "name": "my-mod",
    "version": "1.0.0",
    "author": "YourName",
    "description": "What this mod does",
    "namespace": "mymod",
    "cruhon": ">=0.1.0"
}
```

---

## __init__.py — register(api)

```python
from cruhon.core.ast_nodes import Node, register_node
from dataclasses import dataclass, field

# 1. Yeni bir AST Node tanımla
@dataclass
class SayNode(Node):
    message: str = ""

register_node("SayNode", SayNode)


# 2. Parser fonksiyonu — @say[mesaj] → SayNode
def parse_say(parser):
    line = parser.current.line
    parser.advance()  # @say token'ını tüket
    args = parser.parse_args()
    return SayNode(message=args[0] if args else "", line=line)


# 3. Visitor — SayNode → Python kodu
def visit_say(transpiler, node):
    return transpiler._line(f'print(">> " + str({repr(node.message)}))')


# 4. register(api) — modun giriş noktası
def register(api):
    # Yeni komut ekle
    api.command("say", parse_say, visit_say)

    # Yeni kütüphane ekle
    # api.lib("redis", "redis")
    # api.lib_call("redis", "get", lambda args: f"redis_client.get({args[0]})")

    # Core komutu override et
    # api.override("print", my_print_visitor)

    # Hook'lara bağlan
    # api.hook("before_run", setup_function)
    # api.hook("after_run", cleanup_function)
    # api.hook("on_error", error_handler)
```

Kullanım (bir .clpy dosyasında):
```
@say[Hello from my mod!]
```

---

## Hook Events

| Event              | Ne zaman tetiklenir        | Parametre         |
|--------------------|---------------------------|-------------------|
| `before_run`       | Program başlamadan önce   | `source`          |
| `after_run`        | Program bittikten sonra   | —                 |
| `before_parse`     | Lexer'dan önce            | kaynak string     |
| `after_parse`      | Parse bittikten sonra     | AST ProgramNode   |
| `before_transpile` | Transpile öncesi          | AST ProgramNode   |
| `after_transpile`  | Python kodu üretilince    | Python string     |
| `on_error`         | Hata oluşunca             | `error`           |

---

## pip Modu Olarak Yayınlama

```
pip install cruhon-db
```

Paket adın `cruhon-` ile başlamalı.
`__init__.py` içinde `register(api)` fonksiyonu olmalı.
Cruhon otomatik bulur ve yükler.

---

## Namespace Çakışması

İki mod aynı `@komut` adını kullanırsa son yüklenen kazanır.
Çakışmadan kaçınmak için namespace kullan:

```
@mymod.komut[...]
```

---

## Örnek Modlar

- `cruhon-db` — SQLite/PostgreSQL desteği
- `cruhon-discord` — discord.py sarımı  
- `cruhon-web` — Flask/FastAPI sarımı
- `cruhon-redis` — Redis desteği
- `cruhon-dotenv` — .env dosyası desteği
