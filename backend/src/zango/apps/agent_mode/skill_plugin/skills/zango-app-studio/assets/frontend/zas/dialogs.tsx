// Every write goes through the crud package's own FormRenderer (server-driven forms,
// sync for show_when, validation errors) or a plain confirm POST. Never a hand-built form.
import React, { useState } from "react";
import { FormRenderer } from "@zango-core/crud/form";
import { ArrowRightCircle, CircleX, Plus, Pencil, Tag as TagIcon, Zap } from "lucide-react";
import * as api from "./api";
import { useToast } from "./ui";
import { Button, Modal } from "./kit";

export type FormSpec =
  | { kind: "create"; endpoint: string; title: string; params?: Record<string, string> }
  | { kind: "row"; endpoint: string; title: string; uuid: string; actionKey: string }
  | { kind: "transition"; endpoint: string; title: string; uuid: string; engineName: string; danger?: boolean }
  | { kind: "tag"; endpoint: string; title: string; uuid: string; tag: string; state: "enabled" | "disabled" };

function paramsFor(f: FormSpec): { get: Record<string, string>; post: Record<string, string> } {
  switch (f.kind) {
    case "create":
      return { get: { action: "initialize_form", ...(f.params || {}) }, post: { form_type: "create_form", ...(f.params || {}) } };
    case "row":
      return {
        get: { action: "initialize_form", action_type: "row", action_key: f.actionKey, object_uuid: f.uuid },
        post: { action_type: "row", form_type: "row_action_form", action_key: f.actionKey, object_uuid: f.uuid },
      };
    case "transition":
      return {
        get: { view: "workflow", action: "initialize_form", transition_type: "status", transition_name: f.engineName, object_uuid: f.uuid },
        post: { view: "workflow", action: "process_transition", transition_type: "status", transition_name: f.engineName, object_uuid: f.uuid },
      };
    case "tag":
      return {
        get: { view: "workflow", action: "initialize_form", transition_type: "tag", transition_name: f.tag, transition_state: f.state, object_uuid: f.uuid },
        post: { view: "workflow", action: "process_transition", transition_type: "tag", transition_name: f.tag, transition_state: f.state, object_uuid: f.uuid },
      };
  }
}

const iconFor = (f: FormSpec) =>
  f.kind === "create" ? <Plus /> : f.kind === "row" ? <Pencil /> : f.kind === "tag" ? <TagIcon /> : (f as any).danger ? <CircleX /> : <ArrowRightCircle />;

/** A server-driven form in a modal. onDone gets the response (object_uuid on create). */
export function FormDialog({ spec, onClose, onDone }: { spec: FormSpec; onClose: () => void; onDone: (res: any) => void }) {
  const toast = useToast();
  const p = paramsFor(spec);
  const endpoint = spec.endpoint.split("?")[0];
  return (
    <Modal title={spec.title} icon={iconFor(spec)} iconTone={spec.kind === "transition" && spec.danger ? "red" : undefined} wide onClose={onClose}>
      <div className="zas-form-host">
        <FormRenderer
          api_endpoint={endpoint}
          getParams={p.get}
          postParams={p.post}
          skipAutoRefresh
          onResponse={(res: any) => {
            const r = api.body(res) ?? res;
            if (res?.success === false) return;
            toast(r?.message || "Saved");
            onDone(r);
          }}
          onError={(e: Error) => toast("Could not load the form", e.message, true)}
        />
      </div>
    </Modal>
  );
}

/** Yes/no, then one POST. Used for transitions and tags without a form, and confirm row actions. */
export function ConfirmDialog({ title, message, confirmLabel, danger, run, onClose, onDone }: {
  title: string; message: string; confirmLabel: string; danger?: boolean;
  run: () => Promise<any>; onClose: () => void; onDone: (res: any) => void;
}) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const go = async () => {
    setBusy(true); setErr(null);
    try {
      const res = await run();
      const r = api.body(res) ?? {};
      if (res?.success === false) {
        setErr(r?.message || (typeof r === "string" ? r : "That didn't work. Try again or reload the page."));
        return;
      }
      toast(r?.message || "Done");
      if (r?.url) window.open(r.url, "_blank", "noopener");
      onDone(r);
    } catch (e: any) {
      setErr(String(e?.message || e));
    } finally {
      setBusy(false);
    }
  };
  return (
    <Modal title={title} subtitle={message} icon={danger ? <CircleX /> : <Zap />} iconTone={danger ? "red" : undefined} onClose={onClose}
      footer={<>
        <Button onClick={onClose}>Cancel</Button>
        <Button variant={danger ? "danger-primary" : "primary"} onClick={go} disabled={busy}>{busy ? "Working…" : confirmLabel}</Button>
      </>}>
      {err && <div className="zas-note bad" role="alert">{err}</div>}
    </Modal>
  );
}

/** Holds whichever dialog is open. `open` takes a ready element so callers stay declarative. */
export function useDialog() {
  const [el, setEl] = useState<React.ReactNode>(null);
  return { dialog: el, open: (node: React.ReactNode) => setEl(node), close: () => setEl(null) };
}
