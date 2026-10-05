# Plan: Bot de Noticias de IA en Telegram (100% gratis, 100% nube)

## Objetivo
Recibir en el celular, vía Telegram, las noticias más frescas de IA (EEUU, China, mundo),
traducidas al español, sin necesidad de tener ningún equipo corriendo localmente.

## MVP (Mínimo Producto Viable)
Versión más simple que ya funciona:
- 3-4 fuentes RSS de noticias de IA
- Filtro de noticias ya vistas (sin duplicados)
- Traducción título + resumen al español (Google Translate, gratis)
- Envío a un único chat de Telegram
- Ejecución automática cada 15 min en la nube

## Arquitectura

```
GitHub Actions (cron cada 15 min, repo público → minutos ilimitados)
        |
        v
Python: feedparser (lee RSS)
        |
        v
Filtro: JSON/SQLite con IDs de noticias ya enviadas (guardado en el repo)
        |
        v
Traducción: deep-translator (Google Translate, gratis, sin API key)
        |
        v
Telegram Bot API → tu chat personal → llega a tu celular
```

## Componentes

### 1. Bot de Telegram
- Crear con @BotFather → obtener TOKEN
- Obtener tu CHAT_ID (hablar con @userinfobot o @getmyid_bot)
- Ambos se guardan como Secrets en GitHub: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`

### 2. Fuentes (RSS, gratis)
- The Verge (IA): https://www.theverge.com/rss/index.xml
- TechCrunch (IA): https://techcrunch.com/category/artificial-intelligence/feed/
- Hacker News (filtrado por IA)
- Reddit r/artificial y r/LocalLLaMA (RSS)
- Blogs oficiales: OpenAI, Anthropic, Google DeepMind, Hugging Face
- China (fase 3): Pandaily, SCMP Tech

### 3. Filtro de duplicados
- Archivo `seen.json` en el repo con los links/IDs ya enviados
- Al final de cada ejecución, el workflow hace commit y push de los actualizados

### 4. Traducción
- Librería Python `deep-translator` (Google Translate, gratis, sin API key)
- Traduce título y resumen/descripción del RSS al español

### 5. Automatización
- GitHub Actions con cron `*/15 * * * *`
- **Repo público**: minutos de Actions ilimitados y gratis
- Secrets cifrados aunque el repo sea público (TOKEN y CHAT_ID seguros)
- Cache de pip para acelerar cada ejecución

## Fases de desarrollo

**Fase 1 — MVP funcional**
1. Crear bot en Telegram y obtener token + chat ID
2. Script Python: leer RSS → filtrar → traducir → enviar mensaje
3. Probar ejecutándolo una vez en local
4. Subir a GitHub y activar el cron

**Fase 2 — Estabilizar**
5. Persistencia de `seen.json` entre ejecuciones
6. Formato del mensaje: 📰 Título traducido + resumen corto + link + fuente
7. Manejo de errores (fuente caída, límite de traducción)

**Fase 3 — Temáticas**
8. Clasificador por keywords → publicar en topics distintos
   (grupo de Telegram en modo Forum: Noticias, Investigación, Empresas, China)
9. Fuentes en inglés + chinas priorizadas para "lo más fresco"

**Fase 4 — Mejoras opcionales**
10. Resúmenes con LLM (Ollama no aplica en nube gratis; alternativa: API free tier)
11. Modo digest (resumen 2-3 veces al día en vez de tiempo real)
12. Migrar a Cloudflare Workers o VPS Oracle si se necesita más frecuencia

## Decisiones tomadas
| Tema | Decisión |
|---|---|
| Hosting | GitHub Actions (nube, gratis) |
| Notificación | Telegram → celular |
| Traducción | Google Translate vía deep-translator (gratis) |
| Formato | Híbrido: resumen corto + link (fase 2+) |
| Frecuencia | Tiempo real aproximado (cada 15 min) |
| Costo | $0 |

## Limitaciones conocidas
- GitHub Actions cron no es exacto al minuto (puede haber algunos min de retraso)
- deep-translator puede fallar ocasionalmente (límite de Google) → reintentar
- GitHub Actions puede pausar workflows programados en repos sin actividad >60 días → hacer commits esporádicos

## Stack
- Python 3.11+
- feedparser, deep-translator, python-telegram-bot (o requests directo a la API)
- GitHub Actions + GitHub Secrets
