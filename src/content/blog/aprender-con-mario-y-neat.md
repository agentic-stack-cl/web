---
title: "Aprender a fondo con IA: cómo entendí redes neuronales viendo a Mario morir"
description: "Cómo usar LLMs como tutores y compañeros de laboratorio para dominar conceptos complejos (NEAT y memoria) a través de hipótesis y datos."
pubDate: 2026-11-08
authors: [qnelo]
tags: [aprendizaje, ia-agentica, neuroevolucion, experimentos]
draft: false
cover: "../../assets/blog/aprender-con-mario-y-neat/termina-1-1.jpg"
coverAlt: "Mario completando el nivel 1-1 en la generación 42 mediante una red neuronal recurrente"
---

Casi todo el mundo usa asistentes de código de la misma forma: pedir una función, copiarla, pegarla y seguir adelante si compila. Ahorra tiempo, pero tiene una trampa silenciosa: si dejas que la inteligencia artificial piense por ti, terminas produciendo software más rápido mientras entiendes menos lo que construyes.

Existe una alternativa mucho más potente: **darle la vuelta a la herramienta**. Usar los modelos de lenguaje no como generadores de código descartable, sino como tutores socráticos, asistentes de instrumentación científica y calibradores de hipótesis para aprender temas difíciles desde sus cimientos.

Hace poco decidí entender de verdad cómo aprende una red neuronal. Había completado cursos teóricos sobre vectores, retropropagación y transformers, pero nunca había visto a una red aprender desde cero. Para lograrlo, me propuse reproducir un experimento clásico: entrenar una red neuronal mediante neuroevolución para jugar _Super Mario Bros._ de NES, usando a un modelo de IA como compañero de investigación.

<figure class="my-8">
  <video
    controls
    muted
    playsinline
    preload="metadata"
    poster="/blog/aprender-con-mario-y-neat/primeras-generaciones.jpg"
    class="w-full rounded-xl shadow-md"
  >
    <source src="/blog/aprender-con-mario-y-neat/primeras-generaciones.mp4" type="video/mp4" />
    Tu navegador no soporta la reproducción de video HTML5.
  </video>
  <figcaption class="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">
    Generaciones 5 a 40 de la corrida que completó el nivel. A la izquierda, el juego en tiempo real; a la derecha, lo que percibe la red, las conexiones activas y la curva de fitness.
  </figcaption>
</figure>

## El experimento: MarI/O y NEAT

En 2015, SethBling publicó [MarI/O](https://www.youtube.com/watch?v=qv6UVOQ0F44), un video donde una red neuronal aprendía sola a completar un nivel de _Super Mario World_ mediante un algoritmo llamado **NEAT** (_NeuroEvolution of Augmenting Topologies_). Quise reproducirlo en Linux con _Super Mario Bros._ (NES) usando un emulador y Python (`stable-retro` y `neat-python`).

A diferencia del aprendizaje supervisado tradicional, NEAT no aprende a partir de millones de ejemplos etiquetados ni requiere calcular gradientes:

1. **La red no mira la pantalla**: procesar píxeles crudos a 60 cuadros por segundo exigiría convoluciones pesadas, y un modelo multimodal tardaría segundos por decisión. En su lugar, el entorno lee la memoria RAM del emulador de NES y resume el entorno en una **grilla de 13×13 casillas** centrada en Mario: `1` para bloques sólidos, `-1` para enemigos y `0` para espacio vacío. Esas 169 casillas entran a la red junto a una señal adicional (si el botón A estaba presionado en la decisión previa). Las 6 salidas representan los botones del mando: A, B, Arriba, Abajo, Izquierda y Derecha.
2. **Neuroevolución en acción**: una población de 300 redes juega en paralelo. Cada una recibe una calificación (**fitness**) basada en qué tan a la derecha llegó Mario, penalizando el tiempo transcurrido y otorgando un bono de 1.000 puntos al tocar la bandera.
3. **Selección y mutación**: las redes con mejor puntuación tienen descendencia. Las hijas mutan: cambian el peso de sus conexiones, añaden nuevos enlaces o incorporan neuronas intermedias.
4. **Especies**: NEAT agrupa las redes parecidas en especies para que una mutación estructural nueva (por ejemplo, una neurona recién nacida con pesos débiles) no compita de inmediato contra redes consolidadas, dándole tiempo para madurar.

Al principio, la IA escribió la base del código (`mario.py`, `entrenar.py`, `ver.py`). Mi trabajo fue hacer las preguntas, correr los entrenamientos y analizar los resultados.

## El quiebre: la tesis antes que el experimento

En la primera corrida dejé entrenar 1.000 generaciones. El resultado fue frustrante: Mario se estancó en $x = 2.850$, a corta distancia de la bandera (en $x = 3.161$), y durante las últimas 270 generaciones la población no mejoró ni un solo píxel.

Podría haberle pedido a la IA que "arreglara el código" mágicamente. En su lugar, cambiamos la dinámica de trabajo: **le pedí que estructurara cada cambio como una tesis con hipótesis y predicciones medibles antes de ejecutar el entrenamiento**.

Escribir la predicción antes de correr cambia las reglas del juego:

- **Elimina el sesgo de retrospectiva**: cuando una corrida termina, no puedes inventar una justificación de por qué "hizo lo esperado". Lo que dijiste que pasaría está escrito.
- **Pone a prueba la comprensión del modelo**: te obliga a evaluar si el razonamiento técnico de la IA es sólido o si solo está sugiriendo cambios al azar.
- **Te obliga a entender el mecanismo**: no tocas un parámetro sin saber exactamente qué efecto físico o matemático esperas ver en el gráfico.

A lo largo del proyecto formulamos 14 predicciones antes de lograr que Mario completara el nivel.

## Mover una perilla y medir el impacto

Cada corrida modificó una única variable conceptual. Cada fallo dejó un aprendizaje concreto.

### 1. El colapso de las especies (Corrida 2)

Durante 897 de las 1.000 generaciones de la corrida inicial existieron apenas 2 o 3 especies activas. En la configuración de NEAT teníamos `species_elitism = 2`, lo que significa que el algoritmo nunca elimina a las 2 mejores especies. Como solo había 2 especies, **ninguna podía extinguirse jamás**, aunque llevaran 300 generaciones sin aportar ninguna mejora.

- **Hipótesis**: una población que pierde diversidad genética deja de explorar caminos alternativos.
- **Perilla**: convertimos `compatibility_threshold` (la distancia genómica que define si dos redes pertenecen al mismo grupo) en un umbral dinámico que se autoajusta para sostener entre 8 y 16 especies vivas. Además, redujimos `species_elitism` a 1.
- **Resultado**: el 93 % de las generaciones mantuvo la diversidad objetivo y el récord subió más rápido, aunque todavía no lograba completar el nivel.
- **Aprendizaje**: la diversidad en algoritmos genéticos no es un detalle estético; es el motor que evita que la población quede atrapada en óptimos locales.

### 2. La mutación que destruía el conocimiento (Corrida 3)

Al revisar las curvas de la corrida 2 noté un síntoma visual: la brecha entre el mejor individuo y el promedio de la población se hacía cada vez más ancha. Le mostré la gráfica a la IA y pregunté la causa.

En vez de dar una respuesta teórica genérica, el modelo midió el fenómeno: tomó la mejor red de esa generación, generó 1.500 variantes con los parámetros de mutación activos y las puso a jugar en el emulador. **Solo el 10,5 % de los hijos conservaba al menos el 95 % del rendimiento de su padre**. La mutación era tan agresiva que alteraba cerca del 90 % de los pesos sinápticos en cada salto generacional, destruyendo los reflejos adquiridos.

- **Perilla**: ajustamos la tasa de mutación a una distribución suave, asegurando que la mayoría de los hijos heredaran pesos casi intactos con variaciones marginales.
- **Resultado**: la curva promedio subió de inmediato y la población se volvió mucho más consistente.
- **Aprendizaje**: observar un síntoma macroscópico (la distancia entre dos líneas en un gráfico) y pedirle a la IA que diseñe un experimento microscópico (medir la retención en 1.500 hijos) es una combinación imbatible.

### 3. La trampa del atajo frente a la red con memoria (Corrida 4)

Hacia el final del nivel 1-1, Mario debe cruzar precipicios que requieren saltos largos. Para saltar lejos en la NES, hay que mantener presionado el botón A durante 20 a 30 cuadros continuos.

La red evaluaba la grilla cada 5 cuadros. Aunque le habíamos dado una entrada para saber si A estaba presionado en el cuadro inmediatamente anterior, la red era estrictamente _feedforward_ (hacia adelante): no tenía memoria interna de estados previos.

Había dos caminos posibles para resolverlo:

1. **El atajo humano**: programar un sensor artificial en el código que calculara si Mario estaba en el aire y forzara el salto.
2. **El principio evolutivo**: habilitar redes recurrentes (`feed_forward = False` en `neat.cfg`), permitiendo que las conexiones formen ciclos y las neuronas retengan su estado anterior.

El primer camino resolvía el nivel rápido, pero no me enseñaba nada sobre redes neuronales; era simplemente programar la solución a mano. Elegimos el segundo camino.

El resultado fue contundente: **en la generación 42, una red completó el nivel y tocó la bandera**, superando los 3.360 puntos de fitness.

<figure class="my-8">
  <video
    controls
    muted
    playsinline
    preload="metadata"
    poster="/blog/aprender-con-mario-y-neat/termina-1-1.jpg"
    class="w-full rounded-xl shadow-md"
  >
    <source src="/blog/aprender-con-mario-y-neat/termina-1-1.mp4" type="video/mp4" />
    Tu navegador no soporta la reproducción de video HTML5.
  </video>
  <figcaption class="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">
    La red de la generación 45 completando el nivel 1-1 con un fitness de 3.366,5 puntos.
  </figcaption>
</figure>

Lo más revelador vino después: al inspeccionar la arquitectura de la red ganadora descubrimos que no había creado ciclos complejos. En una red recurrente evaluada por pasos, las neuronas ocultas alimentan el siguiente ciclo con el valor calculado en el instante anterior. Ese retraso de un único paso temporal era toda la memoria que Mario necesitaba para sostener el salto en el momento exacto. Si desconectábamos ese retraso temporal, el puntaje de la misma red caía de 3.366 a 369 puntos.

## 7 reglas para aprender temas complejos con IA

Este experimento dejó un marco de trabajo que ahora aplico cada vez que quiero dominar una tecnología o concepto nuevo:

1. **Pregunta lo que no sabes tal como lo piensas**: no pierdas tiempo fingiendo vocabulario técnico. Las preguntas ingenuas ("¿la red ve píxeles o números?", "¿por qué estas dos líneas se separan?") revelan los supuestos fundamentales que necesitas ordenar primero.
2. **Pide explicaciones con tus propios datos**: una lección teórica sobre estancamiento genético en Wikipedia se olvida rápido; una explicación que usa la gráfica de las corridas que acaban de fallar en tu CPU queda grabada para siempre.
3. **Escribe la predicción antes de ejecutar**: formula la hipótesis por escrito. Si aciertas, confirmas tu modelo mental; si fallas, descubres una laguna de conocimiento que de otro modo habrías pasado por alto.
4. **Tú observas los síntomas, la IA mide los datos**: los humanos somos muy buenos detectando patrones visuales anómalos en gráficos y pantallas. Los modelos son excelentes escribiendo scripts para aislar 1.500 casos de prueba y medir la desviación estándar.
5. **Separa explicar de hacer**: usa la instrucción _"solo dímelo, no toques el código"_. Si dejas que el asistente edite los archivos en cada mensaje, pasarás de aprender a ser un mero espectador de git diffs.
6. **Define qué es trampa**: la IA siempre buscará el camino más corto hacia el objetivo que le des. Si tu objetivo es pasar el nivel, te sugerirá trucos en Python; si tu objetivo es comprender cómo aprende una red, debes fijar la regla de buscar soluciones algorítmicas genuinas.
7. **Elige el camino que enseña**: ante dos alternativas de diseño, escoge la que te obligue a entender el principio de funcionamiento subyacente antes que la que resuelva el síntoma por la vía rápida.

## El rol del programador en la era de los agentes

En un mundo donde los agentes de IA pueden escribir miles de líneas de código en minutos, el valor del ingeniero no radica en recordar sintaxis de memoria, sino en **formular las preguntas correctas, diseñar experimentos rigurosos y comprender a fondo los principios de los sistemas que construye**.

Usar la inteligencia artificial para aprender no disminuye tu criterio; lo multiplica.

---

## Referencias

- SethBling (2015). [MarI/O - Machine Learning for Video Games](https://www.youtube.com/watch?v=qv6UVOQ0F44).
- Stanley, K. O., & Miikkulainen, R. (2002). [Evolving Neural Networks through Augmenting Topologies](https://nn.cs.utexas.edu/downloads/papers/stanley.ec02.pdf). _Evolutionary Computation_, 10(2), 99-127.
- Documentación de NEAT en Python: [neat-python](https://neat-python.readthedocs.io/).
