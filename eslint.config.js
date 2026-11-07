import js from "@eslint/js";
import tseslint from "typescript-eslint";
import astro from "eslint-plugin-astro";
import globals from "globals";

export default [
  { ignores: ["dist/", ".astro/", "node_modules/", "public/vendor/"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...astro.configs.recommended,
  ...astro.configs["jsx-a11y-strict"],
  {
    languageOptions: { globals: { ...globals.browser, ...globals.node } },
  },
  {
    // Scripts inline del radar: usan la API global de radar.js
    files: ["src/pages/radar/index.astro"],
    languageOptions: { globals: { radar_visualization: "readonly", d3: "readonly" } },
  },
];
