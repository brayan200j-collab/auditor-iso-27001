/** Architecture rules for the web app (see CLAUDE.md section 6). */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "features-only-through-index",
      comment: "A feature may use another feature only through its public index.ts.",
      severity: "error",
      from: { path: "^src/features/([^/]+)/" },
      to: {
        path: "^src/features/([^/]+)/.+",
        pathNot: ["^src/features/$1/", "^src/features/[^/]+/index\.ts$"],
      },
    },
    {
      name: "app-imports-features-via-index",
      comment: "Routes compose features through their index.ts only.",
      severity: "error",
      from: { path: "^src/app/" },
      to: { path: "^src/features/[^/]+/.+", pathNot: "^src/features/[^/]+/index\.ts$" },
    },
    {
      name: "ui-is-leaf",
      comment: "Base UI components do not know about features, routes or the API.",
      severity: "error",
      from: { path: "^src/components/ui/" },
      to: { path: "^src/(features|app|lib/api|lib/auth)/" },
    },
    {
      name: "supabase-only-in-auth",
      comment: "Supabase is used only for authentication.",
      severity: "error",
      from: { pathNot: "^src/(lib/auth/|proxy\.ts)" },
      to: { path: "@supabase/" },
    },
    {
      name: "no-features-from-lib",
      severity: "error",
      from: { path: "^src/lib/" },
      to: { path: "^src/(features|app)/" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    exclude: { path: "(\.next|node_modules|schema\.d\.ts)" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    enhancedResolveOptions: {
      exportsFields: ["exports"],
      conditionNames: ["import", "require", "node", "default", "types"],
    },
  },
};
