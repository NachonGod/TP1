# TP1

# Slither de los papus

## Descripción

Este proyecto es un juego desarrollado en Python utilizando la librería Pygame, inspirado en el clásico Slither.io.
Permite jugar de forma local con hasta 4 jugadores y también incluye bots controlados por inteligencia artificial.

El objetivo del juego es controlar una serpiente, comer comida para crecer y evitar chocar contra otras serpientes o los bordes del mapa, intentando matar a las otras serpientes.

---

## Controles

* Jugador 1: Mouse (click izquierdo = turbo)
* Jugador 2: W A S D (doble W = turbo)
* Jugador 3: Flechas (doble ↑ = turbo)
* Jugador 4: T F G H (doble T = turbo)
* ESC / P: Pausar el juego

---

## Características principales

* Movimiento fluido con física basada en ángulos
* Multijugador local (hasta 4 jugadores)
* Bots con inteligencia artificial avanzada
* Sistema de turbo con duración y cooldown
* Sistema de comida y crecimiento progresivo
* Colisiones y muerte con efectos de partículas
* Minimapa en tiempo real
* Scoreboard en vivo
* Selector de nombres y colores
* Guardado de resultados en archivo JSON
* Sonidos del juego (comer, morir, inicio)

---

## Inteligencia Artificial

Los bots implementan:

* Evitación de bordes
* Detección de colisiones (raycast)
* Evasión de otras serpientes
* Búsqueda de comida segura
* Movimiento autónomo

---

## Tecnologías utilizadas

* Python 
* Pygame

---

## Cómo ejecutar el juego

1. Instalar Python 
2. Instalar Pygame:

```
pip install pygame
```

3. Ejecutar el archivo principal:

```
python main.py
```

---

## Desarrollo

El proyecto fue desarrollado a lo largo de 3 semanas, organizando el trabajo de forma progresiva:

* Semana 1: Base del juego y movimiento
* Semana 2: Jugabilidad y colisiones
* Semana 3: IA, interfaz y mejoras finales

Los avances se subieron a GitHub semanalmente.

---

## Estado del proyecto

Finalizado y funcional

---

## Autor

Proyecto realizado por Manuel Mañé Mazzieri de 4AO para un traba practico.
