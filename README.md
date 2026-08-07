# ⚫⚪ JuveDaily

Un sistema automatizado que arma un resumen diario de noticias de la Juventus, clasificado por la fiabilidad de quién reportó cada dato, y lo entrega directo a Telegram — sin tener que revisar decenas de mensajes sueltos de un canal para saber qué es rumor y qué es información seria.

## Qué hace

Todos los días a las 8:00 PM (hora de Venezuela) — cuando ya se asienta el día noticioso — el sistema:

1. **Descarga los mensajes recientes** del canal de Telegram [@GJustjuve](https://t.me/GJustjuve), que agrega noticias y filtraciones de mercado sobre la Juventus.
2. **Le pide a Gemini** (la API gratuita de Google) que revise cada mensaje y lo clasifique según quién lo reportó, descartando todo lo que no tenga una fuente identificable.
3. **Entrega el resultado** por Telegram, con el nombre de cada periodista o diario resaltado en negrita y subrayado para distinguirlo del resto del texto.

Todo corre solo, sin intervención manual, usando GitHub Actions como programador de tareas.

## Cómo clasifica las noticias

En vez de organizar por tema (fichajes, lesiones, etc.), el resumen agrupa cada noticia según la fiabilidad de quien la reportó:

- **⭐ Tier 1** — Romeo Agresti, Fabrizio Romano, Gianluca Di Marzio
- **🥈 Tier 2** — Nicolò Schira, Giovanni Albanese, Alfredo Pedullà, Ciro Di Natale, Matteo Moretto, @_Morik92_
- **📰 Periódicos** — Sky Sport, Tuttosport, Gazzetta dello Sport

Si un mensaje no menciona a ninguno de estos nombres, se descarta directamente — no entra al resumen. Cada categoría muestra como máximo los 10 mensajes más recientes.

## Cómo se ve

> **📅 Juventus - 06 de agosto de 2026**
>
> **⭐ Tier 1**
> • **_Romeo Agresti_**: Giuntoli y Manna trabajan activamente en Milán en el mercado de fichajes.
>
> **🥈 Tier 2**
> • **_Nicolò Schira_**: La Juventus acelera por Zirkzee, con el Manchester United abierto a un préstamo con opción de compra.
>
> **📰 Periódicos**
> • **_Gazzetta dello Sport_**: La búsqueda de un portero top se pospone hasta 2027 por limitaciones económicas.

## Arquitectura

| Componente | Rol |
|---|---|
| `fetch_data.py` | Descarga los mensajes recientes de GJustjuve |
| `generate_briefing.py` | Le pasa los mensajes a Gemini, que clasifica y redacta, y lo envía por Telegram |
| GitHub Actions | Ejecuta todo el flujo automáticamente cada noche |
| Telegram Bot API | Entrega el resumen con formato enriquecido (HTML) |

## Stack

- **Python** — descarga, filtrado y distribución
- **Google Gemini API** (`gemini-2.5-flash`) — clasificación por fuente y redacción del resumen
- **Telegram Bot API** — entrega diaria con formato HTML
- **GitHub Actions** — automatización con cron diario (8:00 PM Venezuela)

## Por qué existe

Seguir un canal de Telegram con decenas de mensajes al día sobre fichajes y
