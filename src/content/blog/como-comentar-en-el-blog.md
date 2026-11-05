---
title: "Cómo crear tu cuenta de GitHub y comentar en el blog"
description: "Guía paso a paso, sin conocimientos técnicos, para crear una cuenta de GitHub y dejar comentarios en los posts de The Agentic Stack."
pubDate: 2026-11-05
authors: [sebmaldo]
tags: [guia, github, comunidad]
---

Los comentarios del blog funcionan con **GitHub**, una plataforma donde se guarda y comparte código. No necesitas saber programar para usarla: solo una cuenta gratuita. Elegimos este sistema porque no tiene publicidad, no rastrea a quien lee y no nos obliga a mantener un servidor propio.

Esta guía te lleva desde cero hasta tu primer comentario. Toma unos cinco minutos.

## 1. Crea tu cuenta de GitHub

1. Entra a [github.com/signup](https://github.com/signup).
2. Escribe tu correo, una contraseña segura y un **nombre de usuario**. El nombre de usuario será visible junto a tus comentarios, así que elige uno que te represente.
3. Resuelve la verificación que te pide GitHub para confirmar que eres una persona.
4. Revisa tu correo: GitHub te envía un código para confirmar la dirección. Escríbelo donde te lo pida.
5. GitHub puede hacerte algunas preguntas sobre cómo usarás la cuenta. Puedes responderlas o saltarlas; no afectan lo que necesitas para comentar.

Te recomendamos activar la **verificación en dos pasos** (_Settings → Password and authentication_). Protege tu cuenta aunque alguien conozca tu contraseña.

## 2. Comenta en un post

1. Abre cualquier post del blog y baja hasta la sección **Comentarios**.
2. Presiona **Iniciar sesión con GitHub** (_Sign in with GitHub_).
3. GitHub te pedirá autorizar a **giscus**, la herramienta que conecta los comentarios del blog con GitHub. Revisa lo que solicita y presiona **Authorize**. Esto se hace una sola vez.
4. Vuelves al post con la sesión iniciada. Escribe tu comentario y presiona **Comentar**.

También puedes reaccionar con emojis a los comentarios de otras personas o al post mismo, sin escribir nada.

### Si prefieres no autorizar giscus

Cada post tiene una conversación asociada en las [Discussions del repositorio](https://github.com/agentic-stack-cl/web/discussions). Puedes entrar ahí con tu cuenta de GitHub y comentar directamente; el comentario aparece igual en el blog.

## 3. Dale formato a tu comentario

Los comentarios aceptan **Markdown**, una forma simple de dar formato con texto:

| Escribes                           | Se ve                            |
| ---------------------------------- | -------------------------------- |
| `**negrita**`                      | **negrita**                      |
| `_cursiva_`                        | _cursiva_                        |
| `[un enlace](https://ejemplo.com)` | [un enlace](https://ejemplo.com) |
| `` `código` ``                     | `código`                         |

Usa la pestaña **Vista previa** antes de publicar para revisar cómo quedará.

## Preguntas frecuentes

**¿Mis comentarios son públicos?** Sí. Cualquier persona puede leerlos, en el blog y en GitHub, junto a tu nombre de usuario y tu foto de perfil.

**¿Puedo editar o borrar un comentario?** Sí. En la caja de comentarios, el enlace del comentario te lleva a GitHub; ahí aparece el menú **⋯** con las opciones para editarlo o eliminarlo.

**¿Cómo quito el acceso a giscus?** En GitHub ve a _Settings → Applications → Authorized OAuth Apps_, elige giscus y presiona **Revoke**. Tus comentarios anteriores se mantienen.

**¿Tiene costo?** No. La cuenta de GitHub y los comentarios son gratuitos.

Si algo no te funciona, cuéntanos en el Discord o en las [Discussions](https://github.com/agentic-stack-cl/web/discussions) y te ayudamos.
