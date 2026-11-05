export const SITE = {
  name: "The Agentic Stack",
  url: "https://agenticstack.cl",
  description:
    "Comunidad chilena de desarrolladores que explora el desarrollo de software agéntico: radar tecnológico, blog y conversación abierta.",
  lang: "es",
  locale: "es_CL",
  github: "https://github.com/agentic-stack-cl",
  repo: "https://github.com/agentic-stack-cl/web",
  /**
   * Invitación permanente al servidor de Discord (sin caducidad ni límite de usos; entra
   * a #bienvenida-y-reglas). Si es null, los botones "Únete" llevan a /comunidad#unete.
   */
  discordInvite: "https://discord.gg/P247bN6tms" as string | null,
} as const;

export const NAV = [
  { href: "/", label: "Inicio" },
  { href: "/radar", label: "Radar" },
  { href: "/blog", label: "Blog" },
  { href: "/comunidad", label: "Comunidad" },
] as const;

/** giscus: comentarios sobre GitHub Discussions de agentic-stack-cl/web. */
export const GISCUS = {
  repo: "agentic-stack-cl/web",
  repoId: "R_kgDOVjYHJA",
  // TODO(owners): crear la categoría "Comentarios del blog" (formato Announcement)
  // y reemplazar category + categoryId. Ver docs/DEPLOY.md.
  category: "Announcements",
  categoryId: "DIC_kwDOVjYHJM4DKaX1",
  mapping: "pathname",
  lang: "es",
} as const;

/** Slug del post que explica cómo crear una cuenta de GitHub y comentar. */
export const COMMENT_GUIDE_SLUG = "como-comentar-en-el-blog";

export const joinHref = SITE.discordInvite ?? "/comunidad#unete";
