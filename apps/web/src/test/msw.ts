import { setupServer } from "msw/node";

/** Shared MSW server for component tests; each test registers its own handlers. */
export const server = setupServer();
