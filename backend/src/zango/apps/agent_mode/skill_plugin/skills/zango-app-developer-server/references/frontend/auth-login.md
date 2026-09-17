# Branded Login Page

Every Zango app you build ships a **branded login page**. Always — there is no
toggle and no condition. The login screen is the first thing anyone sees; the
framework default says nothing about the product.

This file gives you the **auth contract** (get this wrong and nobody can log in)
and then the layout.

> Read §1–§4 before writing a single line of CSS.

---

## 1. Wiring

Register a full override of the framework's `LoginPage` on `ZangoApp`:

```jsx
// src/App.tsx
import { ZangoApp } from '@zango-core/crm-framework';
import * as customPages from './custom/pages';
import AppLoginCard from './custom/auth/AppLoginCard';

const ZApp: any = ZangoApp;   // the shipped .d.ts lags the runtime props

const App = () => (
  <ZApp
    appInitializerEndpoint="/app/initializer/"
    customPages={customPages}
    authConfig={{ customComponents: { LoginPage: AppLoginCard } }}
  />
);
```

Pass the **component**, not an element — the framework renders it as
`<LoginPage />`. Passing `<AppLoginCard />` breaks it.

> The app must serve **its own build** for this to have any effect. If
> `backend/app/templates/app.html` still loads the prebuilt `appbuilder` bundle,
> your login component is not in the served JavaScript and the page renders the
> stock login with no error. See SKILL.md STEP 5e.

## 2. Use the framework's auth primitives — never hand-roll auth

```jsx
import {
  PasswordLoginForm,     // the real form: username/email, password, remember-me
  RoleSelection,         // multi-role picker
  PasswordResetRequired, // first login / expired password
  authService,           // .setPassword(), .selectRole()
  getNextParam,          // reads ?next= from the URL
  getValidRedirectUrl,   // safely resolves where to land
} from '@zango-core/crm-framework';
```

Your component owns the **layout**; these own the **auth**. Never POST to a login
endpoint yourself: you would lose SAML, multi-step callbacks
(`?token&request_id`), password policy, rate limiting and role selection.

These exports may be missing from the shipped type declarations — add
`// @ts-ignore` above the import rather than reimplementing them.

## 3. Drive the flow from `onSuccess` — not `LoginContext.onLogin`

**`LoginContext.onLogin` mis-handles the single-role case.** Drive the flow from
`PasswordLoginForm`'s `onSuccess` instead.

After a successful password check the backend may still require another step.
That `next_step` object arrives in **four different response shapes** depending on
how the backend answered, so normalise before reading it:

```jsx
const extractNextStep = (result) => {
  if (result?.status === 401 && result?.data) return result.data?.next_step;
  if (result?.next_step) return result.next_step;
  return (result?.response?.data || result?.data || result)?.next_step;
};
```

Handle each pending step:

| `next_step.id` | Meaning | Render |
|---|---|---|
| `set_password`, `password_expiry`, `first_login` | Password must be set now | `<PasswordResetRequired>` |
| `role_selection` | User holds more than one role | `<RoleSelection>` |
| anything else (`mfa`, …) | Not handled here | log a warning; do not silently succeed |

No pending step means auth is complete — redirect:

```jsx
const goAfterAuth = (result) => {
  const nextParam = getNextParam(window.location.search);
  const serverRedirect =
    result?.redirect_url || result?.response?.data?.redirect_url || result?.data?.redirect_url;
  window.location.href = getValidRedirectUrl(nextParam, serverRedirect, '/app');
};
```

Always resolve through `getValidRedirectUrl` — it rejects open-redirect targets.

`roles` in `role_selection` metadata may be an **array or an object map**; handle
both, or a multi-role user gets an empty picker:

```jsx
let rolesArray = [];
if (Array.isArray(nextStep.metadata?.roles)) rolesArray = nextStep.metadata.roles;
else if (typeof nextStep.metadata?.roles === 'object')
  rolesArray = Object.entries(nextStep.metadata.roles)
    .map(([id, name]) => ({ id, name, is_default: false }));
```

After a password reset the backend may return a **further** step (often
`role_selection`), so route the result back through the same handler rather than
redirecting blindly.

## 4. Verify before you call it done

- A user with **one** role logs in and lands on `/app`.
- A user with **two** roles sees the picker and can choose.
- A **first-login** user is asked to set a password, and completes.

If you cannot exercise these, say so explicitly in your summary.

## 5. Layout — the split-screen archetype

This is the house style. Re-theme it and rewrite the copy; do not invent a
different layout.

```
┌───────────────────────────┬────────────────────────┐
│  brand mark + product     │                        │
│                           │   WELCOME BACK         │
│  Headline about the       │   Sign in to <App>     │
│  domain outcome           │   ┌──────────────────┐ │
│                           │   │ email            │ │
│  ◉──◉──◉──◉  journey      │   │ password         │ │
│                           │   │ [   Sign in   ]  │ │
│  ✓ value line             │   └──────────────────┘ │
│  ✓ value line             │                        │
│  Powered by Zelthy        │   staff access only    │
└───────────────────────────┴────────────────────────┘
     hidden below 880px           always visible
```

- **Left** — brand mark, product name, a headline naming the *domain outcome*,
  and 3–5 value lines or journey steps. Hidden under 880px.
- **Right** — `<PasswordLoginForm />` inside a card, with a kicker + heading.
- Keep the **"Powered by Zelthy"** attribution.

### Copy rules

Write about **this app's domain**, from the requirement spec. Never generic
filler ("Welcome to our portal", "Login to continue").

- Good: *"From first consent to confident self-care."*
- Bad: *"Welcome! Please sign in to continue."*

Use only the brand name, tagline and palette the requirement spec or app theme
supplies. **Never reproduce a real third-party company's branding, logos or
trade dress** — if the spec names a real organisation, use its name as plain text
and nothing more.

### Styling constraints

- One `<style>{CSS}</style>` block inside the component and inline SVG for icons.
  **No new npm packages, no external fonts, no CDN** — the build allowlist
  forbids installing anything.
- Source the palette from the app theme (`useAppContext().theme`, or the
  `--color-brand-500` CSS variables the initializer sets) so login and app agree.
- Scope every rule under one root class (`.app-login`) — this component mounts
  over the whole viewport.
- You are styling **framework-rendered** internals: target
  `input:not([type=checkbox])`, `button[type=submit]`, `label`. The password
  reveal control is a `type=button`, so a `button[type=submit]` rule will not
  catch it.
- `RoleSelection` and `PasswordResetRequired` each ship their **own centred card
  and heading**. Inside your card that reads as a card-in-a-card with the title
  said twice — strip their chrome (`.max-w-lg` wrapper) and hide their heading.

> **Put media queries last.** Overrides such as `.creative { display: none }` have
> the same specificity as the base rule they fight, so **source order alone**
> decides the winner. A media query placed above the base rule silently loses and
> the left panel never hides on mobile.

## 6. Skeleton to copy

```jsx
// src/custom/auth/AppLoginCard.tsx
import { useState } from 'react';
// @ts-ignore - auth exports are absent from the shipped type declarations
import {
  PasswordLoginForm, RoleSelection, PasswordResetRequired,
  authService, getNextParam, getValidRedirectUrl,
} from '@zango-core/crm-framework';

const CSS = `
.app-login{position:fixed;inset:0;z-index:9000;overflow:auto;
  font-family:Inter,system-ui,sans-serif;color:#14171F;
  --brand:#5048ED;--brand-600:#4038D6;--border:#EEF0F4;--page:#F8F9FB;--sub:#4A4F5C}
.app-login *{box-sizing:border-box}
.app-login .shell{display:grid;grid-template-columns:1.05fr .95fr;min-height:100vh;background:var(--page)}
.app-login .creative{display:flex;flex-direction:column;padding:56px 60px;color:#fff;
  background:linear-gradient(150deg,#1B1846,#2C2777 52%,var(--brand))}
.app-login .headline{margin-top:auto}
.app-login .headline h1{font-size:42px;line-height:1.1;letter-spacing:-.035em;margin:0 0 16px;max-width:15ch}
.app-login .panel{display:flex;align-items:center;justify-content:center;padding:40px}
.app-login .box{width:100%;max-width:424px}
.app-login .authcard{background:#fff;border:1px solid var(--border);border-radius:14px;
  padding:32px 30px 26px;box-shadow:0 16px 40px -18px rgba(44,39,119,.16)}
.app-login .authcard h2{font-size:24px;font-weight:700;letter-spacing:-.025em;margin:0 0 6px}
.app-login .authcard input:not([type=checkbox]):not([type=radio]){
  width:100%;height:44px;border:1.5px solid var(--border);border-radius:10px;padding:0 14px;
  font-size:14px;background:#FBFCFE;outline:none}
.app-login .authcard input:not([type=checkbox]):not([type=radio]):focus{
  border-color:var(--brand);background:#fff;box-shadow:0 0 0 3.5px rgba(80,72,237,.13)}
.app-login .authcard button[type=submit]{width:100%;height:44px;border:none;border-radius:10px;
  cursor:pointer;font-size:14px;font-weight:600;color:#fff;
  background:linear-gradient(135deg,var(--brand),var(--brand-600))}
/* strip the nested card RoleSelection / PasswordResetRequired bring with them */
.app-login .authcard .max-w-lg{max-width:none!important;margin:0!important;padding:0!important}
.app-login .authcard .max-w-lg > div{background:transparent!important;border:none!important;
  box-shadow:none!important;padding:0!important}
.app-login .authcard .max-w-lg div:has(> h3){display:none}
/* responsive MUST come last - equal specificity, source order decides */
@media (max-width:880px){
  .app-login .shell{grid-template-columns:1fr}
  .app-login .creative{display:none}
}
@media (max-width:480px){
  .app-login .panel{padding:24px 18px}
  .app-login .authcard{padding:24px 20px 20px}
}
`;

const extractNextStep = (result: any) => {
  if (result?.status === 401 && result?.data) return result.data?.next_step;
  if (result?.next_step) return result.next_step;
  return (result?.response?.data || result?.data || result)?.next_step;
};

const goAfterAuth = (result: any) => {
  const nextParam = getNextParam(window.location.search);
  const serverRedirect =
    result?.redirect_url || result?.response?.data?.redirect_url || result?.data?.redirect_url;
  window.location.href = getValidRedirectUrl(nextParam, serverRedirect, '/app');
};

const AppLoginCard = () => {
  const [showRoleSelection, setShowRoleSelection] = useState(false);
  const [roles, setRoles] = useState<any[]>([]);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [showPasswordReset, setShowPasswordReset] = useState(false);
  const [passwordPolicy, setPasswordPolicy] = useState<any>(null);
  const [resetReason, setResetReason] = useState('');

  const handleSuccess = (result: any) => {
    const nextStep = extractNextStep(result);

    if (nextStep?.is_pending) {
      if (['set_password', 'password_expiry', 'first_login'].includes(nextStep.id)) {
        setPasswordPolicy(nextStep.metadata?.password_policy || null);
        setResetReason(nextStep.metadata?.reason || 'Please set your password');
        setUserInfo(result?.loginUser || result?.user || {});
        setShowPasswordReset(true);
        return;
      }
      if (nextStep.id === 'role_selection') {
        let rolesArray: any[] = [];
        if (Array.isArray(nextStep.metadata?.roles)) rolesArray = nextStep.metadata.roles;
        else if (typeof nextStep.metadata?.roles === 'object')
          rolesArray = Object.entries(nextStep.metadata.roles)
            .map(([id, name]) => ({ id, name, is_default: false }));
        setRoles(rolesArray);
        setUserInfo(result?.data?.user || result?.user || result?.loginUser || {});
        setShowRoleSelection(true);
        return;
      }
      console.warn('AppLoginCard: unsupported pending auth step', nextStep.id, result);
      return;
    }
    goAfterAuth(result);
  };

  const handlePasswordReset = async (d: any) => {
    const result = await authService.setPassword(d.password);
    if (extractNextStep(result)?.is_pending) {
      setShowPasswordReset(false);
      handleSuccess(result);
      return;
    }
    goAfterAuth(result);
  };

  const handleRoleSelect = async (role: any) =>
    goAfterAuth(await authService.selectRole(role.id));

  return (
    <div className="app-login">
      <style>{CSS}</style>
      <div className="shell">
        <section className="creative">
          {/* brand mark + product name */}
          <div className="headline">
            <h1>{/* domain outcome headline - rewrite per app */}</h1>
            <p>{/* one sentence on what the app does for whom */}</p>
          </div>
          <div style={{ marginTop: 'auto', opacity: .55, fontSize: 11 }}>Powered by Zelthy</div>
        </section>

        <section className="panel">
          <div className="box">
            <div className="authcard">
              {showPasswordReset ? (
                <>
                  <h2>Set your password</h2>
                  <PasswordResetRequired
                    reason={resetReason}
                    passwordRules={passwordPolicy ? {
                      minLength: passwordPolicy.min_length || 8,
                      requireUppercase: passwordPolicy.require_uppercase || false,
                      requireLowercase: passwordPolicy.require_lowercase || false,
                      requireNumbers: passwordPolicy.require_numbers || false,
                      requireSpecialChars: passwordPolicy.require_special_chars || false,
                    } : undefined}
                    onReset={handlePasswordReset}
                  />
                </>
              ) : showRoleSelection ? (
                <>
                  <h2>Select your role</h2>
                  <RoleSelection user={userInfo} roles={roles} onRoleSelect={handleRoleSelect} />
                </>
              ) : (
                <>
                  <h2>Sign in to {/* app name */}</h2>
                  <PasswordLoginForm onSuccess={handleSuccess} />
                </>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AppLoginCard;
```

## 7. Checklist

- [ ] `authConfig.customComponents.LoginPage` set, component (not element)
- [ ] `app.html` loads the app's own bundle, not appbuilder's
- [ ] `AnonymousUsers` granted on `AppView` and `RedirectAppView` in `policies.json`
- [ ] Flow driven by `onSuccess`, not `LoginContext.onLogin`
- [ ] `extractNextStep` handles all four response shapes
- [ ] `role_selection` handles roles as array **and** object map
- [ ] Redirect resolved through `getValidRedirectUrl`
- [ ] Copy names the app's real domain outcome; no generic filler
- [ ] Palette sourced from the app theme; no new packages, fonts or CDN
- [ ] Media queries last; left panel hides below 880px
- [ ] Verified: single-role, multi-role, and first-login users
