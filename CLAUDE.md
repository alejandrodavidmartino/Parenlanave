# CLAUDE.md — contexto del proyecto

## Sobre mí y cómo quiero que me ayudes
- Soy Alejandro, desarrollador junior en prácticas. Este proyecto es para jugar con amigos y para mi portfolio/CV.
- Respóndeme en español.
- Después de cada comando que me des, explica brevemente qué hace y por qué se usa.
- Quiero entender el código, no solo copiarlo: explica las decisiones de diseño.

## El proyecto
Juego web de estimación numérica por turnos (inspirado en un juego de mesa, pero con nombre, diseño y preguntas propias: **no usar el nombre, diseño ni preguntas del juego original**). Nombre del repo provisional: `Proyecto1Povisional`.

## Stack y herramientas
- Python 3.13/3.14, Django 6.1 (actualizar a 6.2 LTS cuando salga, abril 2027).
- Gestor de dependencias: **uv** (`pyproject.toml` + `uv.lock`, entorno `.venv`). Usar `uv add`, `uv add --dev`, `uv run`, `uv sync`. No usar pip directamente.
- Frontend: Tailwind CSS vía **django-tailwind-cli** (sin Node) + **HTMX** con **django-htmx**. Diseño mobile-first; posible PWA más adelante.
- Base de datos: SQLite en local, PostgreSQL en producción. Configuración con **django-environ** (`.env` no se sube al repo).
- Calidad: **pytest + pytest-django + pytest-cov**, **Ruff** (lint + formato), **pre-commit**.
- Depuración: django-debug-toolbar.
- Más adelante: whitenoise, Docker, GitHub Actions, despliegue en Render/Railway/Fly.io.

## Convenciones
- Entorno: Windows + VS Code.
- Código, nombres de ramas y commits en **inglés**.
- Flujo: ramas `feature/...` y pull requests hacia `main`.

## Arquitectura (decisión clave)
- La lógica del juego vive en un **motor en Python puro** (p. ej. `game/engine.py`), sin importar nada de Django. Solo stdlib (`dataclasses`, `enum`).
- Las vistas de Django son finas: cargan estado → llaman al motor → guardan resultado.
- El mismo motor se reutilizará en la Fase 2 (online).
- La aleatoriedad se inyecta (`random.Random(seed)`) para que los tests sean deterministas.
- La puntuación es una función separada, `score_round(result) -> dict[player, int]`, que devuelve deltas. Quien aplica los deltas impone el mínimo de 0 monedas: `max(0, coins + delta)`.

## Reglas del juego (nuestra versión)
Por ronda:
1. Aparece una pregunta con respuesta numérica.
2. El primer jugador dice un número y se convierte en capitán. Quién abre cada ronda se elige **al azar**.
3. Por turnos, cada jugador que siga en la nave elige:
   - **Subirse/quedarse**: apoya la apuesta actual.
   - **Bajarse**: queda fuera hasta el final de la ronda (no puede volver).
   - **Subir la apuesta**: dice un número **estrictamente mayor** y pasa a ser el nuevo capitán.
4. Tras una subida, todos los que siguen en la nave vuelven a decidir cuando les toca (ocurre de forma natural porque el turno da la vuelta completa antes de volver al capitán).
5. La ronda termina cuando el turno vuelve al capitán sin que nadie haya subido. El capitán no puede subir su propia apuesta. Si todos los demás se bajan, la ronda termina igualmente al volver el turno al capitán.
6. Se revela la respuesta: la misión es un éxito si la apuesta del capitán es **≤ respuesta real**.

Modelo de estado del motor:
- `PlayerStatus`: `ON_BOARD` | `LEFT` (no hace falta un estado "pendiente").
- La ronda guarda: `captain`, `current_bid`, `turn_index`.

Puntuación: **pendiente de definir** (habrá casos de éxito, fracaso y capitán solitario, con números propios). El saldo nunca baja de 0.

Fuera de la Fase 1 (se añadirá después en su propia rama): regla especial de "órdago" (apuesta exacta que congela la ronda).

## Plan
**Fase 1 — un solo dispositivo** (el móvil se va pasando y la app indica de quién es el turno):
1. Esqueleto: proyecto Django con uv, app `game`, Ruff, pre-commit, pytest, Tailwind.
2. Motor de reglas en Python puro + tests de cada regla.
3. Modelos `Question` (texto, respuesta numérica, categoría opcional) y `Game`, gestionados desde el admin.
4. Vistas con HTMX: crear partida, añadir jugadores, pantalla de turno.
5. Fin de ronda: revelar respuesta y pasar a la siguiente.

**Fase 2 — online con salas**: polling con HTMX primero, luego WebSockets con Django Channels. Puntuación completa.

## Documentación pendiente
- Escribir `RULES.md` con las reglas definitivas (fuente de verdad para los tests: cada regla, un test).
