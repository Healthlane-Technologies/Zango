// Branded login (split screen), built from spec.ui.json: app name, description,
// modules as feature rows, roles as the middle band. Auth itself is the framework's
// own PasswordLoginForm / RoleSelection / PasswordResetRequired (never hand-rolled;
// references/zango/entity-360.md and references/zango/frontend/auth-login.md).
// Wire it in App.tsx: authConfig={{ customComponents: { LoginPage: ZasLogin } }}
import { useState } from "react";
// @ts-ignore - auth exports are missing from the shipped type declarations
import { PasswordLoginForm, RoleSelection, PasswordResetRequired, authService, getNextParam, getValidRedirectUrl } from "@zango-core/appbuilder";
import { Layers, ShieldCheck, Workflow } from "lucide-react";
import { SPEC, applyTheme } from "./config";
import "./fonts.css";
import "./tokens.css";

const CSS = `
.zas-login{position:fixed;inset:0;z-index:9000;overflow:auto;font-family:var(--z-font);color:var(--z-text);background:var(--z-ground)}
.zas-login *{box-sizing:border-box}
.zas-login .shell{display:grid;grid-template-columns:1.05fr .95fr;min-height:100vh}
.zas-login .creative{position:relative;overflow:hidden;display:flex;flex-direction:column;gap:28px;padding:52px 56px;color:#fff;
  background:radial-gradient(1200px 600px at 110% -10%,color-mix(in srgb,var(--brand) 55%,transparent),transparent 60%),
             linear-gradient(155deg,color-mix(in srgb,var(--brand) 30%,#0b0d14),color-mix(in srgb,var(--brand) 70%,#0b0d14) 55%,var(--brand))}
.zas-login .creative::after{content:"";position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.08) 1px,transparent 1px);background-size:22px 22px;pointer-events:none}
.zas-login .creative>*{position:relative;z-index:1}
.zas-login .mark{display:flex;align-items:center;gap:12px;font-weight:650;font-size:15px}
.zas-login .mark i{width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.25);display:grid;place-items:center;font-style:normal;font-weight:700}
.zas-login .eyebrow{font-size:11.5px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;opacity:.75}
.zas-login h1{font-size:40px;line-height:1.1;letter-spacing:-.035em;font-weight:700;margin:8px 0 12px;max-width:640px;text-wrap:balance}
.zas-login .lede{font-size:15px;line-height:1.55;opacity:.82;max-width:52ch;margin:0}
.zas-login .band{display:flex;flex-wrap:wrap;gap:8px}
.zas-login .band span{font-size:12.5px;font-weight:550;padding:6px 11px;border-radius:999px;background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.2)}
.zas-login .feats{display:flex;flex-direction:column;gap:14px;margin-top:auto}
.zas-login .feat{display:flex;gap:12px;align-items:flex-start}
.zas-login .feat .ic{width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,.14);display:grid;place-items:center;flex:none}
.zas-login .feat .ic svg{width:17px;height:17px}
.zas-login .feat b{display:block;font-size:14px;font-weight:600}
.zas-login .feat span{display:block;font-size:13px;opacity:.75;line-height:1.45}
.zas-login .foot{font-size:11px;opacity:.55}
.zas-login .panel{display:flex;align-items:center;justify-content:center;padding:40px}
.zas-login .box{width:100%;max-width:424px}
.zas-login .box .eyebrow{color:var(--z-muted);opacity:1;margin-bottom:8px}
.zas-login .authcard{background:var(--z-card);border:1px solid var(--z-bd);border-radius:14px;padding:32px 30px 26px;box-shadow:0 16px 40px -18px color-mix(in srgb,var(--brand) 30%,transparent)}
.zas-login .authcard h2{font-size:24px;font-weight:700;letter-spacing:-.025em;margin:0 0 6px}
.zas-login .authcard .hint{color:var(--z-muted);font-size:13.5px;margin:0 0 20px}
.zas-login .authcard input:not([type=checkbox]):not([type=radio]){width:100%;height:44px;border:1.5px solid var(--z-bd);border-radius:10px;padding:0 14px;font-size:14px;background:#fbfcfe;outline:none}
.zas-login .authcard input:not([type=checkbox]):not([type=radio]):focus{border-color:var(--brand);background:#fff;box-shadow:0 0 0 3.5px var(--b100)}
.zas-login .authcard form.form-vertical>.form-item{margin-bottom:14px}
.zas-login .authcard button[type=submit]{width:100%;height:44px;border:none;border-radius:10px;cursor:pointer;font-size:14px;font-weight:600;color:#fff;background:var(--brand)}
.zas-login .authcard button[type=submit]:hover{background:var(--b600)}
.zas-login .authcard .max-w-lg{max-width:none!important;margin:0!important;padding:0!important}
.zas-login .authcard .max-w-lg>div{background:transparent!important;border:none!important;box-shadow:none!important;padding:0!important}
.zas-login .authcard .max-w-lg div:has(>h3){display:none}
@media (max-width:880px){.zas-login .shell{grid-template-columns:1fr}.zas-login .creative{display:none}}
@media (max-width:480px){.zas-login .panel{padding:24px 18px}.zas-login .authcard{padding:24px 20px 20px}}
`;

const extractNextStep = (result: any) => {
  if (result?.status === 401 && result?.data) return result.data?.next_step;
  if (result?.next_step) return result.next_step;
  return (result?.response?.data || result?.data || result)?.next_step;
};
const goAfterAuth = (result: any) => {
  const nextParam = getNextParam(window.location.search);
  const serverRedirect = result?.redirect_url || result?.response?.data?.redirect_url || result?.data?.redirect_url;
  window.location.href = getValidRedirectUrl(nextParam, serverRedirect, "/app");
};
const initials = (s: string) => s.split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
const FEAT_ICONS = [Layers, Workflow, ShieldCheck];

export default function ZasLogin() {
  applyTheme();
  const [step, setStep] = useState<"login" | "reset" | "role">("login");
  const [roles, setRoles] = useState<any[]>([]);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [policy, setPolicy] = useState<any>(null);
  const [reason, setReason] = useState("");
  const app = SPEC.app;

  const handleSuccess = (result: any) => {
    const next = extractNextStep(result);
    if (next?.is_pending) {
      if (["set_password", "password_expiry", "first_login"].includes(next.id)) {
        setPolicy(next.metadata?.password_policy || null);
        setReason(next.metadata?.reason || "Please set your password");
        setUserInfo(result?.loginUser || result?.user || {});
        setStep("reset");
        return;
      }
      if (next.id === "role_selection") {
        let arr: any[] = [];
        if (Array.isArray(next.metadata?.roles)) arr = next.metadata.roles;
        else if (next.metadata?.roles && typeof next.metadata.roles === "object")
          arr = Object.entries(next.metadata.roles).map(([id, name]) => ({ id, name, is_default: false }));
        setRoles(arr);
        setUserInfo(result?.data?.user || result?.user || result?.loginUser || {});
        setStep("role");
        return;
      }
      console.warn("ZasLogin: unsupported pending auth step", next.id, result);
      return;
    }
    goAfterAuth(result);
  };
  const handleReset = async (d: any) => {
    const result = await authService.setPassword(d.password);
    if (extractNextStep(result)?.is_pending) { setStep("login"); handleSuccess(result); return; }
    goAfterAuth(result);
  };
  const handleRole = async (role: any) => goAfterAuth(await authService.selectRole(role.id));

  const feats = (app.modules || []).slice(0, 3);
  return (
    <div className="zas-login" data-zas="login">
      <style>{CSS}</style>
      <div className="shell">
        <section className="creative" aria-hidden="false">
          <div className="mark"><i>{initials(app.name)}</i>{app.name}</div>
          <div>
            <div className="eyebrow">{app.name}</div>
            <h1>{app.description || `Welcome to ${app.name}`}</h1>
            <p className="lede">One place for {feats.map((m) => m.name.toLowerCase()).join(", ") || "your team's work"}, with each person seeing exactly what their role needs.</p>
          </div>
          {app.roles?.length > 0 && <div className="band" aria-label="Built for">{app.roles.map((r) => <span key={r.name}>{r.name}</span>)}</div>}
          <div className="feats">
            {feats.map((m, i) => {
              const Ic = FEAT_ICONS[i % FEAT_ICONS.length];
              return <div className="feat" key={m.code}><div className="ic"><Ic /></div><div><b>{m.name}</b><span>{m.description}</span></div></div>;
            })}
          </div>
          <div className="foot">Powered by Zelthy</div>
        </section>
        <section className="panel">
          <div className="box">
            <div className="eyebrow">{app.name}</div>
            <div className="authcard">
              {step === "reset" ? (
                <>
                  <h2>Set your password</h2>
                  <PasswordResetRequired reason={reason} onReset={handleReset}
                    passwordRules={policy ? {
                      minLength: policy.min_length || 8, requireUppercase: !!policy.require_uppercase, requireLowercase: !!policy.require_lowercase,
                      requireNumbers: !!policy.require_numbers, requireSpecialChars: !!policy.require_special_chars,
                    } : undefined} />
                </>
              ) : step === "role" ? (
                <>
                  <h2>Choose your role</h2>
                  <p className="hint">You have more than one role. Pick the one to work as now.</p>
                  <RoleSelection user={userInfo} roles={roles} onRoleSelect={handleRole} />
                </>
              ) : (
                <>
                  <h2>Sign in</h2>
                  <p className="hint">Use your work email and password.</p>
                  <PasswordLoginForm onSuccess={handleSuccess} />
                </>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
