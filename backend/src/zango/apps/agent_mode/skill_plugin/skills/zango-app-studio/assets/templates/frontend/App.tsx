// src/App.tsx for an App Studio app. Replaces the scaffold's App.tsx in Phase 6.
import { ZangoApp } from "@zango-core/appbuilder";
import * as customPages from "./custom/pages";
import { ZasLogin } from "./zas";

// When .zas/bundle/index.md has a /shell screen, add navbarConfig / topbarConfig here with the
// components in src/custom/shell/ (references/custom-code.md, "The app shell").
// The shipped appbuilder .d.ts lags the runtime props (customPages, authConfig).
const ZApp: any = ZangoApp;

const App = () => (
  <ZApp
    appInitializerEndpoint={"/appbuilder/initializer/"}
    customPages={customPages}
    authConfig={{ customComponents: { LoginPage: ZasLogin } }}
  />
);

export default App;
