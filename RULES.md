# Reglas del juego

Fuente de verdad del motor (`game/engine.py`). Cada regla tiene un identificador
(`R1`, `R2`...) y al menos un test que la comprueba, con el identificador en el nombre
(por ejemplo `test_r14_raise_must_be_higher`).

## Glosario

- **Partida**: el juego completo, formado por varias rondas. Al final gana quien tenga
  más monedas.
- **Ronda**: todo lo que ocurre con una misma pregunta: desde la apuesta inicial hasta
  revelar la respuesta y repartir las monedas. El turno puede dar varias vueltas a la
  mesa dentro de una misma ronda.
- **Turno**: el momento en que un jugador hace una acción (quedarse, bajarse o subir).
- **Barco**: el grupo de jugadores que siguen en juego durante la ronda.
- **Apuesta**: un número que alguien dice como respuesta a la pregunta.
- **Capitán**: el jugador que ha hecho la apuesta más alta hasta el momento.
- **Tripulación**: los jugadores que siguen dentro del barco al final de la ronda, sin
  contar al capitán.
- **Desertores**: los jugadores que se han bajado del barco durante la ronda.

## Partida

- **R1.** Una partida tiene **entre 3 y 8 jugadores**.
- **R2.** Al crear la partida se elige el **número de rondas** (8 por defecto).
- **R3.** Cada jugador empieza la partida con **0 monedas**.
- **R4.** Al terminar la última ronda gana quien tenga **más monedas**. Si hay empate,
  ganan todos los empatados.

## Preparación de la ronda

- **R5.** Al empezar cada ronda, todos los jugadores están **dentro del barco**, también
  los que se bajaron en la ronda anterior.
- **R6.** En cada ronda aparece una pregunta cuya respuesta es un número.
- **R7.** El jugador que abre la ronda se elige **al azar** entre todos los jugadores.
- **R8.** Quien abre dice la **apuesta inicial** y se convierte en **capitán**.

## Apuestas

- **R9.** Una apuesta es un **número entero mayor o igual que 0** (0, 1, 2...). No se
  admiten decimales ni números negativos.

## Turnos

- **R10.** Los turnos siguen el **orden de la lista de jugadores**: después del último va
  el primero, como si estuvieran sentados en círculo. El primer turno es del jugador
  siguiente a quien abrió.
- **R11.** Quien se ha bajado **se salta**: no vuelve a tener turno hasta la ronda
  siguiente.

## Acciones

En su turno, cada jugador que sigue dentro del barco elige una de estas acciones:

- **R12. Quedarse:** apoya la apuesta actual. No cambia nada más y el turno pasa al
  siguiente.
- **R13. Bajarse:** sale del barco hasta el final de la ronda. **No puede volver a
  subir** en esa ronda.
- **R14. Subir la apuesta:** dice un número **estrictamente mayor** que la apuesta actual
  y pasa a ser el **nuevo capitán**. Un número igual o menor no es válido.
- **R15.** El capitán anterior **sigue dentro del barco** como uno más: cuando le toque,
  podrá quedarse, bajarse o volver a subir.
- **R16.** El capitán **no puede subir su propia apuesta**.

## Jugadas no permitidas

- **R17.** La pantalla solo ofrece las jugadas permitidas. Aun así, si al motor le llega
  una jugada no permitida (subir con un número igual o menor, jugar fuera de turno,
  jugar estando bajado, apostar un número no válido...), **la rechaza** y la ronda queda
  **exactamente como estaba**.

## Fin de la ronda

- **R18.** La ronda termina cuando **el turno vuelve al capitán** sin que nadie haya
  subido desde que él lo es. Como cada subida cambia de capitán, todos los que siguen
  dentro vuelven a decidir antes de que la ronda pueda terminar.
- **R19.** Si todos los demás se bajan, la ronda termina igualmente al volver el turno al
  capitán. En ese caso es un **capitán solitario**.

## Resultado

- **R20.** Al terminar la ronda se revela la respuesta real. La misión es un **éxito** si
  la apuesta del capitán es **menor o igual** que la respuesta real, y un **fracaso** si
  es mayor.

  Ejemplo: si la respuesta es 100, apostar 100 es éxito y apostar 101 es fracaso.

## Puntuación

Al terminar la ronda, cada jugador gana o pierde monedas según el resultado:

- **R21. Misión con éxito:** el capitán gana **4**, cada tripulante gana **2** y los
  desertores ganan **0**.
- **R22. Misión fracasada:** el capitán pierde **1**, los tripulantes ganan **0** y cada
  desertor gana **2**.
- **R23. Capitán solitario con éxito:** el capitán gana **6** y los desertores ganan **0**.
- **R24. Capitán solitario fracasado:** el capitán pierde **1** y cada desertor gana
  **2** (igual que R22).
- **R25.** El saldo de monedas de un jugador **nunca baja de 0**: si tiene 0 y pierde
  una, se queda en 0.

## Pregunta del tesoro

- **R26.** Cada ronda tiene un **10 %** de probabilidad de ser una **pregunta del
  tesoro**. Se anuncia al aparecer la pregunta, antes de la primera apuesta.
- **R27.** En una pregunta del tesoro, el **capitán se juega más**: si la misión tiene
  éxito gana **8** (**12** si es solitario) y si fracasa pierde **4**. La tripulación y
  los desertores puntúan como siempre.

## Pendiente de definir

- **Órdago**: regla especial de apuesta exacta que congela la ronda. Se añadirá más
  adelante, en su propia rama.
