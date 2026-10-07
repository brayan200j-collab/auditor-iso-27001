import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";
import jsxA11y from "eslint-plugin-jsx-a11y";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: ["**/*.{js,jsx,mjs,ts,tsx,mts,cts}"],
    rules: {
      ...jsxA11y.flatConfigs.strict.rules,
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-non-null-assertion": "error",
      "react/no-danger": "error",
      "no-restricted-globals": [
        "error",
        {
          name: "fetch",
          message: "Use the typed API client in src/lib/api instead of calling fetch directly.",
        },
      ],
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@supabase/*"],
              message: "Supabase is only used for authentication, inside src/lib/auth.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/lib/api/**", "src/app/api/**", "tests/**", "e2e/**", "src/test/**"],
    rules: { "no-restricted-globals": "off" },
  },
  {
    files: ["src/lib/auth/**", "src/proxy.ts"],
    rules: { "no-restricted-imports": "off" },
  },
  globalIgnores([".next/**", "out/**", "build/**", "next-env.d.ts", "src/lib/api/schema.d.ts"]),
]);

export default eslintConfig;
