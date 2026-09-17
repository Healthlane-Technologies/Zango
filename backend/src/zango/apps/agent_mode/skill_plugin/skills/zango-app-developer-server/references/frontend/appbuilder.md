> **Server-mode note (Agent Mode).** Commands in this file that use
> `docker compose` or the `zango` CLI **cannot be run** in server mode, and
> Bash is otherwise read-only. Treat those as background reference.
> Two exceptions: the **npm commands allowed by STEP 5a and 5f** (scaffold, install,
> build) do run — Node is available — and you run the **`manage.py` commands
> listed in STEP 7** (migrations, sync, static) yourself.

# Zango App Builder Reference

> Auto-generated from documentation pages. Regenerate with: `node scripts/generate-reference.js`

## Quick Start
```bash
npx @zango-core/create-zango-app my-app
cd my-app
cp .env.example .env
npm run dev
```

## Key Imports
```js
import { ZangoApp, useAppContext } from '@zango-core/crm-framework';
import { CrudHandler } from '@zango-core/crud/table';
import { FormRenderer } from '@zango-core/crud/form';
```

## Backend Models
```python
from packages.appbuilder.backend.configure.models import AppRoutesModel, AppMenuModel
from zango.apps.appauth.models import UserRoleModel
```

---


## Quick Start (Getting Started)

**Sections:** Create Your App | Configure Environment | Start Development | Create Your First Custom Page | Add CRUD Page | Build for Production | Available Scripts

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `--verbose` | boolean | - | Print additional logs during scaffolding. |
| `--use-pnpm` | boolean | - | Use pnpm as the package manager. |
| `--skip-install` | boolean | - | Skip installing dependencies after project creation. |
| `VITE_API_BASE_URL` | string | http://localhost:8000 | Backend API URL (use the app domain URL, e.g. `http://yourdomain.com:8000`, not localhost). In dev, the Vite dev server proxies requests here. |
| `VITE_PROXY_ROUTES` | string | /api,/appbuilder | Comma-separated routes to proxy to backend. MUST include `/api` and `/appbuilder`. Add all your CRUD module routes as needed (e.g., /patients, /doctors). |
| `VITE_APP_ENV` | string | development | Environment flag (development / staging / production). |
| `npm run dev` | string | - | Start development server on port 3000 with hot reload and backend proxying. |
| `npm run build` | string | - | Production build to dist/ directory. |
| `npm run build:zango` | string | - | Single-file build for Zango platform deployment (IIFE format). |
| `npm run preview` | string | - | Preview the production build locally. |

### Code Examples

```bash
npx @zango-core/create-zango-app my-app
```

```bash
npm init @zango-core/zango-app my-app
```

```bash
yarn create @zango-core/zango-app my-app
```

```bash
pnpm create @zango-core/zango-app my-app
```

```bash
cd my-appncp .env.example .env
```

```bash
npm run dev
```

```jsx
const Dashboard = () => {
  return (
    <div style={{ padding: 32 }}>
      <h1>Dashboard</h1>
      <p>Welcome to my app!</p>
    </div>
  );
};

export default Dashboard;
```

```jsx
export { default as Dashboard } from './Dashboard';
```

```json
{
  "path": "/app/patients",
  "page_type": "crud",
  "entity": "Patient"
}
```

```bash
npm run build          # Standard build to dist/
npm run build:zango    # Single-file build for Zango platform
```

---

## Project Structure (Getting Started)

**Sections:** Directory Overview | Key Files Explained | Where to Add Code | App.tsx Deep Dive

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `New pages` | string | - | src/custom/pages/YourPage.jsx + export in index.js |
| `Custom components` | string | - | src/custom/components/ |
| `Custom hooks` | string | - | src/custom/hooks/ |
| `Constants / config` | string | - | src/custom/constants/ |
| `Utilities` | string | - | src/custom/utils/ |
| `Assets (images/fonts)` | string | - | src/assets/ |

### Code Examples

```bash
my-app/
├── public/
│   └── favicon.svg
├── src/
│   ├── custom/
│   │   └── pages/              # Your custom pages go here
│   │       ├── Dashboard.jsx
│   │       └── index.js        # Export all custom pages
│   ├── App.tsx                  # Main app - ZangoApp configuration
│   ├── index.tsx                # Dev entry point
│   ├── index.zango.tsx          # Zango platform entry point
│   └── index.css                # Global styles + Tailwind
├── .env                         # Environment config (create from .env.example)
├── .env.example                 # Environment template
├── index.html                   # HTML template
├── package.json
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts               # Dev/production build config
└── vite.config.zango.ts         # Zango single-file build config
```

```tsx
import { ZangoApp } from '@zango-core/crm-framework';
import * as customPages from './custom/pages';

const App = () => {
  return (
    <ZangoApp
      appInitializerEndpoint="/appbuilder/initializer/"
      customPages={customPages}
    />
  );
};

export default App;
```

---

## ZangoApp (App Builder)

**Sections:** Import | Props | Basic Usage | With Full Configuration | Accessing App Data | Layout Configuration | What ZangoApp Does

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `appInitializerEndpoint` | string | /appbuilder/initializer/ | API endpoint for app initialization data. |
| `customPages` | object | - | Map of component names to React components for custom page routing. |
| `layoutConfig` | object | - | Layout configuration: { showTopbar: boolean (true), showNavbar: boolean (true), layoutType: \ |
| `topbarConfig` | object | - | Topbar configuration: { showProfile, customLeftContent, customRightContent, customProfileMenu, customTopbar, profileMenuConfig, className, style } |
| `navbarConfig` | object | - | Navbar configuration: { showLogo, showMenu, isCollapsed, collapsible, customLogo, customMenuContent, customBottomContent, customNavbar, customMenu, menuConfig, className, style } |
| `authConfig` | object | - | Authentication configuration: { customComponents, theme, card, logo, login, roleSelection, twoFactor, resetPassword, providers, messages } |
| `config` | object | - | General app configuration. |
| `customComponents` | object | - | Custom component overrides: { Layout, Topbar, Navbar } |
| `showTopbar` | boolean | true | Show/hide the top navigation bar. |
| `showNavbar` | boolean | true | Show/hide the sidebar navigation. |

### Code Examples

```jsx
import { ZangoApp } from '@zango-core/crm-framework';
```

```jsx
import { ZangoApp } from '@zango-core/crm-framework';
import * as customPages from './custom/pages';

const App = () => (
  <ZangoApp
    appInitializerEndpoint="/appbuilder/initializer/"
    customPages={customPages}
  />
);
```

```jsx
import { ZangoApp } from '@zango-core/crm-framework';
import * as customPages from './custom/pages';
import CustomLogin from './custom/pages/CustomLogin';
import DocsNavbar from './custom/components/DocsNavbar';

const App = () => (
  <ZangoApp
    appInitializerEndpoint="/appbuilder/initializer/"
    customPages={customPages}
    layoutConfig={{
      showTopbar: false,
      showNavbar: true,
      layoutType: 'wide',
    }}
    navbarConfig={{
      collapsible: true,
      customLogo: <MyLogo />,
      customMenu: <DocsNavbar />,
      customBottomContent: <ProfileSection />,
    }}
    topbarConfig={{
      showProfile: true,
      customRightContent: <NotificationBell />,
    }}
    authConfig={{
      customComponents: {
        LoginPage: CustomLogin,
      },
    }}
  />
);
```

```jsx
import { useAppContext } from '@zango-core/crm-framework';

const MyComponent = () => {
  const {
    appData,      // Raw initializer response
    menu,         // Navigation menu items
    routes,       // Application routes
    profileInfo,  // Current user profile
    appLogo,      // App logo URL
    appName,      // Application name
    theme,        // Theme colors & typography
  } = useAppContext();

  return <div>Hello {profileInfo?.name}</div>;
};
```

---

## App Initializer (App Builder)

**Sections:** Overview | Endpoint | Full Response Format | Routes | Menu | Theme | Session Security

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `path` | string | - | URL path, e.g.  |
| `page_type` | string | - | Page renderer:  |
| `component` | string | - | Component name from customPages (for page_type:  |
| `entity` | string | - | Entity name (for page_type:  |
| `route_id` | string | - | UUID for syncing with menu items. |
| `extra_params` | object | - | Additional parameters: { api_endpoint, standalone, ... } |
| `name` | string | - | Display text for the menu item. |
| `uri` | string | - | Navigation URL. |
| `icon` | string | - | SVG string, emoji, or image URL. |
| `children` | array | - | Nested menu items (same structure). |
| `route_id` | string | - | UUID linking to the corresponding route. |
| `enabled` | boolean | - | Enable session timeout monitoring. |
| `ping_url` | string | - | URL to ping on user activity to keep the session alive. |
| `warn_after` | number | - | Seconds of inactivity before showing a timeout warning. |
| `expire_after` | number | - | Seconds of inactivity before auto-logout. |

### Code Examples

```bash
GET /appbuilder/initializer/
```

```json
{
  "success": true,
  "response": {
    "app_name": "My Application",
    "app_version": "1.0.0",
    "app_logo": "/path/to/logo.png",
    "is_user_anonymous": false,
    "user_role": "Admin",
    "session_security_config": {
      "enabled": true,
      "ping_url": "/session_security/ping/",
      "warn_after": 1700,
      "expire_after": 1800
    },
    "metadata": {
      "title": "My App",
      "description": "Application description",
      "favicon": "/favicon.ico"
    },
    "theme": {
      "colors": {
        "primary": "#5048ed",
        "secondary": "#6d7280",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#f04438",
        "gray": "#717680"
      },
      "typography": {
        "font_family": "Inter, sans-serif",
        "font_size_base": "14px",
        "line_height": 1.5
      }
    },
    "routes": [
      { "route_id": "uuid", "path": "/app/dashboard", "page_type": "custom", "component": "Dashboard" },
      { "path": "/app/patients", "page_type": "crud", "entity": "Patient", "extra_params": { "api_endpoint": "/api/patients/" } }
    ],
    "menu": [
      { "name": "Dashboard", "uri": "/app/dashboard", "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M3 10.5 12 3l9 7.5\"/><path d=\"M5 9.5V20a1 1 0 0 0 1 1h14V9.5\"/></svg>" },
      { "name": "Management", "uri": "/app/patients", "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><circle cx=\"12\" cy=\"8\" r=\"4\"/><path d=\"M4 21c0-4 4-7 8-7s8 3 8 7\"/></svg>", "children": [
        { "name": "Patients", "uri": "/app/patients" },
        { "name": "Doctors", "uri": "/app/doctors" }
      ]}
    ],
    "profile_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "mobile": "+1234567890",
      "user_role": "Admin",
      "member_since": "2024-01-01",
      "profile_pic": "/path/to/pic.jpg"
    }
  }
}
```

```css
--color-brand-500: #5048ed;   /* from theme.colors.primary */
--color-gray-500: #717680;    /* from theme.colors.gray */
--color-success-500: #10b981; /* from theme.colors.success */
--color-warning-500: #f59e0b; /* from theme.colors.warning */
--color-error-500: #f04438;   /* from theme.colors.error */
```

---

## Navbar & Topbar (App Builder)

**Sections:** Navbar Configuration | Custom Logo | Custom Menu | Custom Bottom Content | Collapsible Sidebar | Menu Item Format | Topbar Configuration | Hiding Topbar | Custom Topbar Content

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `showLogo` | boolean | true | Show/hide the logo section at the top of the sidebar. |
| `showMenu` | boolean | true | Show/hide the menu items in the sidebar. |
| `isCollapsed` | boolean | false | Start the sidebar in collapsed mode. |
| `collapsible` | boolean | false | Allow the user to toggle collapse with a button. |
| `customLogo` | ReactNode | - | Replace the default logo with a custom component. |
| `customMenu` | ReactNode | - | Replace the entire menu with a custom component. |
| `customMenuContent` | ReactNode | - | Content appended below the menu items. |
| `customBottomContent` | ReactNode | - | Sticky section pinned to the bottom of the sidebar. |
| `customNavbar` | React.ComponentType | - | Replace the entire navbar component. |
| `menuConfig` | object | - | Menu display options. |
| `className` | string | - | Additional CSS class for the navbar container. |
| `style` | CSSProperties | - | Custom inline styles for the navbar container. |
| `showProfile` | boolean | true | Show the profile section with dropdown menu. |
| `showLeftSection` | boolean | true | Show the left section of the topbar. |
| `showRightSection` | boolean | true | Show the right section of the topbar. |
| `customLeftContent` | ReactNode | - | Custom content rendered on the left side of the topbar. |
| `customRightContent` | ReactNode | - | Custom content rendered on the right side (before the profile section). |
| `customProfileMenu` | ReactNode | - | Replace the default profile dropdown content. |
| `customTopbar` | React.ComponentType | - | Replace the entire topbar component. |
| `className` | string | - | Additional CSS class for the topbar container. |
| `style` | CSSProperties | - | Custom inline styles for the topbar container. |

### Code Examples

```jsx
const MyLogo = () => (
  <div style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', gap: 10 }}>
    <img src="/logo.svg" width={28} height={28} />
    <span style={{ fontSize: 16, fontWeight: 700 }}>My App</span>
  </div>
);

<ZangoApp navbarConfig={{ customLogo: <MyLogo /> }} />
```

```jsx
const CustomMenu = () => {
  const location = useLocation();
  const isActive = (uri) => location.pathname.replace(/\/$/, '') === uri.replace(/\/$/, '');

  return (
    <div style={{ padding: '4px 8px' }}>
      <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '1.2px', textTransform: 'uppercase', color: '#98a2b3', padding: '6px 10px' }}>
        SECTION HEADER
      </div>
      <Link to="/app/dashboard" style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '7px 10px',
        borderRadius: 6, backgroundColor: isActive('/app/dashboard') ? '#EAE8FF' : 'transparent',
        color: isActive('/app/dashboard') ? '#5048ED' : '#414651',
        textDecoration: 'none', fontSize: 13, fontWeight: isActive('/app/dashboard') ? 600 : 500,
      }}>
        Dashboard
      </Link>
    </div>
  );
};

<ZangoApp navbarConfig={{ customMenu: <CustomMenu /> }} />
```

```jsx
<ZangoApp navbarConfig={{
  customBottomContent: <ProfileCard />,
}} />
```

```jsx
<ZangoApp navbarConfig={{ collapsible: true }} />
```

```jsx
<ZangoApp layoutConfig={{ showTopbar: false }} />
```

```jsx
<ZangoApp topbarConfig={{
  customLeftContent: <Breadcrumbs />,
  customRightContent: <NotificationBell />,
}} />
```

---

## Routing & Pages (App Builder)

**Sections:** Page Types | Route Configuration | CRUD Pages | Custom Pages | Standalone Pages | Route Matching | Nested Routes | Using CrudHandler in Custom Pages | Backend: Route Model | Backend: Menu Model | Backend: Routes API | Backend: Menu API | Route-Menu Sync | Configuration Panel | settings.json

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `crud` | string | - | Auto-generated CRUD table + detail + forms. Uses CrudHandler internally. |
| `custom` | string | - | Your React component. Loaded from the customPages prop. |
| `login` | string | - | Authentication pages. Rendered standalone (no layout). |
| `training` | string | - | Training module pages. |
| `404` | string | - | Not found page. |
| `path` | string | - | URL path, e.g.  |
| `page_type` | string | - | One of: crud, custom, login, training. |
| `component` | string | - | Component name for custom pages (must match the export name exactly). |
| `entity` | string | - | Entity name for CRUD pages. |
| `extra_params` | object | - | Additional parameters: { api_endpoint, standalone, ... }. |
| `route_id` | string | - | UUID for menu synchronization. |
| `route_id` | string | - | UUID, auto-generated when routes are saved. |
| `name` | string | - | Display name for the route. |
| `path` | string | - | URL path, e.g.  |
| `icon` | string | - | Icon identifier for the route. |
| `page_type` | string | - | One of: login, custom, crud, training. |
| `component` | string | - | Component name for custom page types. |
| `extra_params` | object | - | Additional parameters such as api_endpoint. |
| `route_id` | string | - | UUID linking the menu item to a route for automatic sync. |
| `name` | string | - | Display name for the menu item. |
| `uri` | string | - | URL path the menu item links to. |
| `icon` | string | - | Icon identifier for the menu item. |
| `children` | array | - | Nested child menu items (supports sub-menus). |
| `GET ?action=get_routes` | GET | - | Returns the active routes configuration. |
| `POST ?action=save_routes` | POST | - | Save routes. Auto-assigns route_ids and syncs menus. |
| `PUT ?action=update_routes&pk=ID` | PUT | - | Update an existing routes configuration. |
| `GET ?action=get_configs` | GET | - | Returns all menu configurations. |
| `GET ?action=get_available_roles` | GET | - | Returns roles that do not yet have a menu configured. |
| `POST ?action=create_config` | POST | - | Create a menu for a role. Body: {  |
| `PUT ?action=update_config&pk=ID` | PUT | - | Update an existing menu configuration. |
| `DELETE ?action=delete_config&pk=ID` | DELETE | - | Delete a menu configuration. |
| `package_routes` | array | - | Mount package URL patterns (appbuilder, crud, workflow, etc.) to specific path prefixes. |
| `app_routes` | array | - | Mount app-level URL patterns. Typically a catch-all for the frontend. |

### Code Examples

```json
{
  "path": "/app/patients",
  "page_type": "crud",
  "entity": "Patient",
  "extra_params": {
    "api_endpoint": "/api/patients/"
  }
}
```

```jsx
// src/custom/pages/Analytics.jsx
const Analytics = () => <div>My Analytics Page</div>;
export default Analytics;
```

```jsx
// src/custom/pages/index.js
export { default as Analytics } from './Analytics';
```

```json
{
  "path": "/app/analytics",
  "page_type": "custom",
  "component": "Analytics"
}
```

```json
{
  "path": "/app/public-form",
  "page_type": "custom",
  "component": "PublicForm",
  "extra_params": {
    "standalone": true
  }
}
```

```text
/app/patients                    → Table view
/app/patients/detail-view/:uuid  → Detail view (if enableDetailViewRoute)
```

```jsx
import { CrudHandler } from '@zango-core/crud/table';

const CustomPatientPage = () => (
  <CrudHandler
    api_endpoint="/api/patients/"
    headerProps={{ title: "Patient Management" }}
    customDrawerDetail={MyCustomDetail}
  />
);
export default CustomPatientPage;
```

**Configure Custom Page Routes and Menus via API**

After creating custom pages, you need to configure routes and menus to make them accessible in the AppBuilder frontend.

📖 **See [AppBuilder API Configuration Guide](../packages/appbuilder/api-configuration.md) for complete API details, authentication, and workflows.**

**Custom Page Route Structure:**

```json
{
  "routes": [
    {
      "name": "Dashboard",
      "path": "/app/dashboard",
      "page_type": "custom",
      "component": "Dashboard",
      "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 20V10M10 20V4M16 20v-7M22 20H2\"/></svg>"
    }
  ]
}
```

**Menu Item Structure:**

```json
{
  "menu": [
    {
      "route_id": "custom-page-route-id",
      "name": "Dashboard",
      "uri": "/app/dashboard",
      "icon": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"32\" height=\"32\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.75\"><path d=\"M4 20V10M10 20V4M16 20v-7M22 20H2\"/></svg>",
      "children": []
    }
  ]
}
```

**Important Notes for Custom Pages:**
- `page_type` must be `"custom"`
- `component` field must match the exact export name in `src/custom/pages/index.js`
- Route paths must start with `/app` (e.g., `/app/dashboard`)
- When saving routes, include ALL existing routes + new ones (it replaces all)

**Note:** For CRUD page routes and menus, those are configured as part of the backend development workflow.

```json
{
  "package_routes": [
    { "re_path": "^appbuilder/", "package": "appbuilder", "url": "urls" }
  ],
  "app_routes": [
    { "module": "app", "re_path": "^", "url": "urls" }
  ]
}
```

---

## Authentication (App Builder)

**Sections:** Overview | Auth Configuration | Custom Login Page | Login Configuration | Theme Customization | Role Selection | Two-Factor Authentication | OAuth/OIDC Providers | Password Reset | Custom Component Overrides | Complete Example

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `title` | string | ReactNode | Sign In | Login page title. |
| `subtitle` | string | ReactNode | Sign In | Text displayed below the title. |
| `submitButtonText` | string | Sign In | Submit button label. |
| `rememberMeText` | string | Remember me | Remember me checkbox label. |
| `forgotPasswordText` | string | Forgot password? | Forgot password link text. |
| `otpButtonText` | string | Send OTP | OTP button label. |
| `showRememberMe` | boolean | true | Show or hide the remember me checkbox. |
| `enableTabSwitching` | boolean | true | Allow switching between email and mobile tabs. |
| `redirectAfterLogin` | string | - | Custom redirect URL after successful login. |
| `formLabels` | object | - | Custom labels for form fields: { email, mobile, password }. |
| `formPlaceholders` | object | - | Custom placeholders for form fields: { email, mobile, password }. |
| `tabLabels` | object | - | Custom labels for login tabs: { email, mobile }. |
| `customHeader` | ReactNode | - | Custom content rendered above the login form. |
| `customFooter` | ReactNode | - | Custom content rendered below the login form. |
| `customElementsBelowDescription` | ReactNode[] | - | Elements rendered between the description and the form. |
| `background` | object | - | Background configuration: { color, image, gradient } for the login page. |
| `primaryColor` | string | - | Primary brand color used for buttons and accents. |
| `fontFamily` | string | - | Font family for the auth pages. |
| `borderRadius` | string | - | Global border radius for inputs and buttons. |
| `textColor` | string | - | Primary text color. |
| `linkColor` | string | - | Color for links (forgot password, etc.). |
| `backgroundColor` | string | - | Card background color. |
| `borderRadius` | string | - | Card border radius. |
| `boxShadow` | string | - | Card box shadow. |
| `maxWidth` | string | - | Card maximum width. |
| `padding` | string | - | Card inner padding. |
| `url` | string | - | Logo image URL. |
| `width` | string | - | Logo width. |
| `height` | string | - | Logo height. |
| `title` | string | ReactNode | Continue | Role selection page title. |
| `subtitle` | string | ReactNode | Continue | Subtitle text below the title. |
| `instructionText` | string | Continue | Instruction text for the user. |
| `continueButtonText` | string | Continue | Continue button label. |
| `gridColumns` | 2 | 3 | 2 | Number of columns in grid layout. |
| `customRoleCard` | ReactNode | - | Custom component for rendering individual role cards. |
| `customEmptyState` | ReactNode | - | Custom component shown when no roles are available. |
| `title` | string | ReactNode | 6 | 2FA page title. |
| `subtitle` | string | ReactNode | 6 | Subtitle text below the title. |
| `codeLength` | number | 6 | Number of digits in the OTP code. |
| `resendCountdown` | number | 60 | Seconds before the resend button becomes available. |
| `submitButtonText` | string | Verify | Submit button label. |
| `resendButtonText` | string | Resend Code | Resend button label. |
| `customCodeInput` | ReactNode | - | Custom OTP input component. |
| `customMethodSelector` | ReactNode | - | Custom method selector component (email/SMS toggle). |
| `showProviderIcons` | boolean | true | Show icons on provider buttons. |
| `separatorText` | string | OR | Text shown in the separator between the login form and provider buttons. |
| `customProviderButtons` | object | - | Custom button components keyed by provider name. |
| `LoginPage` | React.ComponentType | - | Replace the entire login page. |
| `LoginCard` | React.ComponentType | - | Replace just the login card within the page. |
| `RoleSelection` | React.ComponentType | - | Replace the role selection page. |
| `TwoFactorAuth` | React.ComponentType | - | Replace the two-factor authentication page. |
| `ForgotPasswordPage` | React.ComponentType | - | Replace the forgot password page. |
| `ResetPasswordPage` | React.ComponentType | - | Replace the reset password page. |
| `OAuthCallbackPage` | React.ComponentType | - | Replace the OAuth callback handling page. |
| `DynamicLoginForm` | React.ComponentType | - | Replace the login form (within the login card). |
| `OTPForm` | React.ComponentType | - | Replace the OTP input form. |
| `ProviderButton` | React.ComponentType | - | Replace the OAuth provider button component. |

### Code Examples

```jsx
<ZangoApp
  authConfig={{
    // Theme, custom components, login config, etc.
  }}
/>
```

```jsx
import CustomLogin from './custom/pages/CustomLogin';

<ZangoApp
  authConfig={{
    customComponents: {
      LoginPage: CustomLogin,
    },
  }}
/>
```

```jsx
<ZangoApp
  authConfig={{
    resetPassword: {
      forgotPassword: {
        title: 'Forgot your password?',
        subtitle: 'Enter your email to receive a reset link.',
        submitButtonText: 'Send Reset Link',
      },
      resetForm: {
        title: 'Set New Password',
        subtitle: 'Choose a strong password for your account.',
        submitButtonText: 'Reset Password',
        passwordRules: 'At least 8 characters with one uppercase and one number.', // pragma: allowlist secret
      },
    },
  }}
/>
```

```jsx
<ZangoApp
  authConfig={{
    theme: {
      background: { gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' },
      primaryColor: '#5048ED',
    },
    logo: { url: '/logo.svg', width: '120px', position: 'center' },
    card: { borderRadius: '16px', boxShadow: '0 20px 60px rgba(0,0,0,0.15)' },
    login: {
      title: 'Welcome Back',
      subtitle: 'Sign in to your account',
      defaultTab: 'email',
      showRememberMe: true,
    },
    providers: {
      buttonStyle: 'outline',
      separatorText: 'or continue with',
    },
  }}
/>
```

---

## Theme & Build (App Builder)

**Sections:** Theme System | Color Configuration | Typography | Backend: Theme Configuration | Using Theme in Custom Components | Tailwind CSS v4 Setup | Build Configuration | Vite Configuration | Entry Points | Django Template Integration | Frontend Build Workflow | Deployment Checklist

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `primary` | string | - | Brand color. Maps to --color-brand-* palette (25 through 950). |
| `secondary` | string | - | Secondary color. |
| `success` | string | - | Success/positive actions. Maps to --color-success-*. |
| `warning` | string | - | Warning states. Maps to --color-warning-*. |
| `error` | string | - | Error/danger states. Maps to --color-error-*. |
| `gray` | string | - | Neutral palette. Maps to --color-gray-*. |
| `background` | string | - | Page background. |
| `text` | string | - | Default text color. |
| `font_family` | string | - | Font family (loaded via Google Fonts or local). |
| `font_size_base` | string | - | Base font size. |
| `line_height` | number | - | Base line height. |

### Code Examples

```css
:root {
  --color-brand-50: #EAE8FF;
  --color-brand-100: #D4D0FF;
  --color-brand-500: #5048ED;   /* primary */
  --color-brand-700: #302AA8;
  --color-brand-900: #151263;

  --color-gray-50: #F9FAFB;
  --color-gray-500: #667085;
  --color-gray-900: #101828;

  --color-success-500: #10B981;
  --color-error-500: #F04438;
  --color-warning-500: #F59E0B;
}
```

```jsx
// Use CSS variables directly in styles
const MyComponent = () => (
  <div style={{
    color: 'var(--color-brand-500)',
    backgroundColor: 'var(--color-gray-50)',
    borderColor: 'var(--color-gray-200)',
  }}>
    Themed content
  </div>
);

// Or with Tailwind (if @theme is configured in CSS)
const MyComponent = () => (
  <div className="text-brand-500 bg-gray-50 border-gray-200">
    Themed content
  </div>
);
```

```css
@import 'tailwindcss';

@theme {
  --color-brand-50: var(--color-brand-50, #EAE8FF);
  --color-brand-500: var(--color-brand-500, #5048ED);
  --color-gray-50: var(--color-gray-50, #F9FAFB);
  --color-gray-500: var(--color-gray-500, #667085);
  /* ... etc */
}
```

```js
// vite.config.ts - Development
{
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': './src' },
  },
  server: {
    port: 3000,
    proxy: { /* from VITE_PROXY_ROUTES */ }
  }
}
```

```js
// vite.config.zango.ts - Zango build
{
  plugins: [react(), cssInjectedByJsPlugin(), viteSingleFile(), tailwindcss()],
  build: {
    rollupOptions: {
      input: 'src/index.zango.tsx',
      output: {
        format: 'iife',
        entryFileNames: 'zango-app.[timestamp].min.js',
        inlineDynamicImports: true,
      }
    },
    minify: 'terser',
    cssCodeSplit: false,
    assetsInlineLimit: 100000000,
  }
}
```

```tsx
function initializeApp() {
  let rootElement = document.getElementById('zango-app')
    || document.getElementById('root');

  if (!rootElement) {
    rootElement = document.createElement('div');
    rootElement.id = 'zango-app';
    document.body.appendChild(rootElement);
  }

  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
```

```html
<div id="zango-app" data-base-path="/app/"></div>
<script>
  window.app_initializer_endpoint = "/appbuilder/initializer/";
</script>
<script type="module" src="{% zstatic 'packages/appbuilder/js/build.min.js' %}"></script>
```

---

## Additional Information (App Builder)

**Sections:** App View (HTML Shell) | URL Configuration | Redirect Flow | Security | Authentication Flow | Reserved Routes | settings.json Reference | Standalone Pages | Root URL Redirect | Extending the App Initializer | Custom App View

### Code Examples

```python
class AppView(TemplateView):
    template_name = "appbuilder/app.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_initializer_endpoint"] = "/app/initializer/"
        context["build_version"] = packages_json.get("version", "0.1.0")
        return context
```

```python
urlpatterns = [
    re_path(r'^initializer/$', AppInitializeAPI.as_view()),  # Reserved
    re_path(r'/', AppView.as_view()),                         # Catch-all SPA
]
```

```json
{
  "version": "1.0.0",
  "package_routes": [
    { "re_path": "^appbuilder/", "package": "appbuilder", "url": "urls" },
    { "re_path": "^crud/", "package": "crud", "url": "urls" }
  ],
  "app_routes": [
    { "module": "app", "re_path": "^", "url": "urls" }
  ]
}
```

```python
from django.shortcuts import redirect
from django.views.generic import View

class RedirectAppView(View):
    def get(self, request, *args, **kwargs):
        return redirect("/app")
```

```python
from django.urls import re_path
from .views import AppView, RedirectAppView, ExtendedAppInitializeAPI

urlpatterns = [
    re_path(r'^app/initializer/$', ExtendedAppInitializeAPI.as_view()),
    re_path(r'^app/', AppView.as_view()),
    re_path(r'^/', RedirectAppView.as_view()),     # Root -> /app
    re_path(r'^login/', RedirectAppView.as_view()), # Legacy login -> /app
]
```

```python
import json
from django.http import HttpResponse
from ...packages.appbuilder.backend.app.views import AppInitializeAPI

class ExtendedAppInitializeAPI(AppInitializeAPI):
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Add custom data to the response
        response_data = json.loads(response.content)
        response_data["response"]["feature_flags"] = {
            "enable_chat": True,
            "enable_analytics": False,
        }

        return HttpResponse(
            json.dumps(response_data),
            status=response.status_code,
            content_type="application/json",
        )
```

```python
from django.views.generic import TemplateView
from zango.core.utils import get_current_role

class AppView(TemplateView):
    template_name = "app.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        if user.is_authenticated:
            context["user_authenticated"] = True
            context["user_name"] = user.name
            context["user_email"] = user.email
            context["role_name"] = get_current_role().name

        return context
```

---
