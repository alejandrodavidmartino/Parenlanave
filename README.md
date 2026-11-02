# ⚓ Atraquen el barco

Juego de fiesta por turnos para jugar con amigos desde un solo móvil. Aparece una pregunta
con respuesta numérica y los jugadores van subiendo la apuesta: gana monedas quien se
acerca a la respuesta **sin pasarse**… o quien abandona el barco a tiempo.

Proyecto personal hecho con **Django + HTMX**, con la lógica del juego separada en un
motor de Python puro y cubierta al 100 % por tests.

## Cómo se juega

1. Sale una pregunta, por ejemplo *«¿Cuántos centímetros de ancho mide una portería de
   fútbol?»*.
2. Un jugador elegido al azar dice un número y se convierte en **capitán**.
3. Por turnos, el resto decide: **quedarse** en el barco, **bajarse** o **subir la
   apuesta** (y convertirse en el nuevo capitán).
4. Cuando el turno vuelve al capitán sin que nadie suba, se revela la respuesta: si la
   apuesta del capitán **no se pasa**, el barco zarpa y la tripulación gana monedas; si
   se pasa, naufraga y ganan los que se bajaron.
5. Tras varias rondas, gana quien tenga más monedas.

Las reglas completas, numeradas de la R1 a la R25, están en [RULES.md](RULES.md).

## Características

- Partidas de 3 a 8 jugadores con un solo dispositivo: la pantalla indica de quién es el
  turno.
- Pantalla de juego que se actualiza sin recargar la página gracias a HTMX.
- Diseño mobile-first con Tailwind CSS.
- Banco de más de 100 preguntas de estimación, gestionable desde el admin de Django.
- Las preguntas no se repiten dentro de una partida.
- La ronda en curso se guarda en la base de datos: si el móvil se bloquea, la partida
  sigue donde estaba.

## Tecnologías

| Área | Herramientas |
|---|---|
| Backend | Python 3.13, Django 6.1 |
| Frontend | HTMX (django-htmx), Tailwind CSS (django-tailwind-cli, sin Node) |
| Base de datos | SQLite en local, PostgreSQL en producción (django-environ) |
| Calidad | pytest, pytest-django, pytest-cov, Ruff, pre-commit |
| Entorno | uv |

## Arquitectura

La decisión principal del proyecto es separar las **reglas del juego** de **Django**:

```
Navegador ──HTMX──► Vista (views.py) ──► Modelo (models.py) ──► Motor (engine.py)
                       fina               carga y guarda          reglas puras
```

- **`game/engine.py`** es un motor en Python puro: no importa nada de Django, solo la
  biblioteca estándar (`dataclasses`, `enum`, `random`). Sabe empezar una ronda, validar
  cada jugada, decidir cuándo termina y puntuar. Cada regla de `RULES.md` tiene al menos un
  test con su número en el nombre (`test_r14_raise_must_be_higher_not_equal`).
- **Los modelos** (`Game`, `Player`, `Question`) guardan el estado y delegan las reglas en
  el motor. La ronda en curso se guarda como JSON.
- **Las vistas son finas**: cargan el estado, llaman al motor y guardan el resultado. Con
  HTMX devuelven solo el tablero; sin él, la página completa.
- **La aleatoriedad se inyecta** (`random.Random(seed)`), así que los tests son
  deterministas.
- **La puntuación** es una función separada que devuelve cuánto gana o pierde cada
  jugador; quien la aplica impide que el saldo baje de 0.

Gracias a esta separación, el mismo motor se podrá reutilizar en una versión online.

## Puesta en marcha

Necesitas [uv](https://docs.astral.sh/uv/) instalado.

```bash
git clone https://github.com/alejandrotfg12/Parenlanave.git
cd Parenlanave
uv sync
```

Copia el fichero de ejemplo de configuración y pon tu propia `SECRET_KEY`:

```bash
cp .env.example .env
```

Crea la base de datos, carga las preguntas y crea un usuario para el admin:

```bash
uv run python manage.py migrate
uv run python manage.py load_questions
uv run python manage.py createsuperuser
```

Arranca el servidor (Django y Tailwind a la vez):

```bash
uv run python manage.py tailwind runserver
```

- Juego: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Tests y calidad

```bash
uv run pytest --cov
```

- 105 tests, con un 100 % de cobertura en la app `game`.
- Ruff para el lint y el formato, ejecutado automáticamente antes de cada commit con
  pre-commit:

```bash
uv run pre-commit install
```

## Estructura

```
config/                  Configuración de Django
game/
├── engine.py            Motor de reglas (Python puro)
├── models.py            Question, Game, Player
├── views.py             Vistas finas
├── forms.py             Formulario de nueva partida
├── templates/game/      Plantillas (_board.html es el tablero que cambia HTMX)
├── data/questions.json  Banco de preguntas
├── management/commands/ Comando load_questions
└── tests/               Tests del motor, modelos, vistas y admin
RULES.md                 Reglas del juego numeradas
```

## Hoja de ruta

- [x] **Fase 1**: partida completa en un solo dispositivo.
- [ ] Despliegue en internet (whitenoise, Docker, GitHub Actions).
- [ ] **Fase 2**: salas online, cada jugador con su móvil (HTMX polling y después Django
  Channels).
- [ ] Regla especial de «órdago»: apuesta exacta que congela la ronda.

## Autor

Alejandro Martino · [GitHub](https://github.com/alejandrotfg12)
