# Reglas del juego

Fuente de verdad del motor (`game/engine.py`). Cada regla tiene un identificador
(`R1`, `R2`...) y al menos un test que la comprueba, con el identificador en el nombre
(por ejemplo `test_r11_raise_must_be_higher`).

## Glosario

- **Nave**: el grupo de jugadores que siguen en juego durante la ronda.
- **Apuesta**: un número que alguien dice como respuesta a la pregunta.
- **Capitán**: el jugador que ha hecho la apuesta más alta hasta el momento.

## Partida

- **R1.** Una partida tiene **entre 3 y 8 jugadores**.

## Preparación de la ronda

- **R2.** Al empezar cada ronda, todos los jugadores están **dentro de la nave**, también
  los que se bajaron en la ronda anterior.
- **R3.** En cada ronda aparece una pregunta cuya respuesta es un número.
- **R4.** El jugador que abre la ronda se elige **al azar** entre todos los jugadores.
- **R5.** Quien abre dice la **apuesta inicial** y se convierte en **capitán**.

## Apuestas

- **R6.** Una apuesta es un **número entero mayor o igual que 0** (0, 1, 2...). No se
  admiten decimales ni números negativos.

## Turnos

- **R7.** Los turnos siguen el **orden de la lista de jugadores**: después del último va
  el primero, como si estuvieran sentados en círculo. El primer turno es del jugador
  siguiente a quien abrió.
- **R8.** Quien se ha bajado **se salta**: no vuelve a tener turno hasta la ronda
  siguiente.

## Acciones

En su turno, cada jugador que sigue dentro de la nave elige una de estas acciones:

- **R9. Quedarse:** apoya la apuesta actual. No cambia nada más y el turno pasa al
  siguiente.
- **R10. Bajarse:** sale de la nave hasta el final de la ronda. **No puede volver a
  subir** en esa ronda.
- **R11. Subir la apuesta:** dice un número **estrictamente mayor** que la apuesta actual
  y pasa a ser el **nuevo capitán**. Un número igual o menor no es válido.
- **R12.** El capitán anterior **sigue dentro de la nave** como uno más: cuando le toque,
  podrá quedarse, bajarse o volver a subir.
- **R13.** El capitán **no puede subir su propia apuesta**.

## Jugadas no permitidas

- **R14.** La pantalla solo ofrece las jugadas permitidas. Aun así, si al motor le llega
  una jugada no permitida (subir con un número igual o menor, jugar fuera de turno,
  jugar estando bajado, apostar un número no válido...), **la rechaza** y la ronda queda
  **exactamente como estaba**.

## Fin de la ronda

- **R15.** La ronda termina cuando **el turno vuelve al capitán** sin que nadie haya
  subido desde que él lo es. Como cada subida cambia de capitán, todos los que siguen
  dentro vuelven a decidir antes de que la ronda pueda terminar.
- **R16.** Si todos los demás se bajan, la ronda termina igualmente al volver el turno al
  capitán. En ese caso es un **capitán solitario**.

## Resultado

- **R17.** Al terminar la ronda se revela la respuesta real. La misión es un **éxito** si
  la apuesta del capitán es **menor o igual** que la respuesta real, y un **fracaso** si
  es mayor.

  Ejemplo: si la respuesta es 100, apostar 100 es éxito y apostar 101 es fracaso.

## Pendiente de definir

- **Puntuación**: habrá casos distintos para éxito, fracaso y capitán solitario. El saldo
  de monedas de un jugador nunca baja de 0.
- **Órdago**: regla especial de apuesta exacta que congela la ronda. Se añadirá más
  adelante, en su propia rama.
