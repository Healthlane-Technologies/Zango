// src/App.tsx for an App Studio app. Replaces the scaffold's App.tsx in Phase 6.
import { ZangoApp } from "@zango-core/appbuilder";
import * as customPages from "./custom/pages";
import { makeLogin } from "./zas";

// When .zas/bundle/index.md has a /shell screen, add navbarConfig / topbarConfig here with the
// components in src/custom/shell/ (references/custom-code.md, "The app shell").
// Open mode (.zas/bundle/prototype/): `import Shell from "./custom/Shell";` and
// customComponents={{ Layout: Shell }} instead (references/open-mode.md, "The shell").
// The shipped appbuilder .d.ts lags the runtime props (customPages, authConfig).
const ZApp: any = ZangoApp;

// The login's left panel. Write both for this app (SKILL.md Phase 6 step 4):
// headline: the outcome in 3–7 words, no full stop ("Every prescription, a case in minutes");
// lede: one sentence on who it is for and what changes for them (at most ~25 words).
const ZasLogin = makeLogin({ headline: "", lede: "" });

const App = () => (
  <ZApp
    appInitializerEndpoint={"/appbuilder/initializer/"}
    customPages={customPages}
    authConfig={{ customComponents: { LoginPage: ZasLogin } }}
  />
);

export default App;
