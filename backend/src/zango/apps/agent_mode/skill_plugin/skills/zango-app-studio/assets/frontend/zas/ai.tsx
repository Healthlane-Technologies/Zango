// AI helpers in the running app (spec ai.agents; zas_core/ai.py does the work). The same surfaces the
// Studio preview shows: a ✦ button on the record header, list rows and the list header, a suggestion
// card to Use or Discard, an "Ask AI" chat, a `type: ai` tab or panel, and "Fill from …" in forms.
// A background run is polled every 2s (backing off) until it is done; nothing here blocks a save.
import React, { useEffect, useRef, useState } from "react";
import { Loader, MessageCircle, Send, Sparkles } from "lucide-react";
import * as api from "./api";
import type { AiClick, AiRun, AiSuggestion } from "./api";
import { Button, Modal } from "./kit";
import { useToast } from "./ui";

const ACTIVE = new Set(["queued", "running"]);
const WAITS = [1500, 2000, 3000, 5000, 8000];

/** Poll a run until it is no longer queued or running. */
export async function settle(endpoint: string, run: AiRun, alive: () => boolean = () => true): Promise<AiRun> {
  let r = run, i = 0;
  while (ACTIVE.has(r.status) && alive()) {
    await new Promise((res) => setTimeout(res, WAITS[Math.min(i++, WAITS.length - 1)]));
    if (!alive()) break;
    r = await api.aiPoll(endpoint, r.id);
  }
  return r;
}

const esc = (s: string) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c] as string));
/** A small, safe markdown subset (bold, italics, code, headings, bullet and numbered lists). */
export function mdHTML(src: string): string {
  const inline = (t: string) => esc(t).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/(^|\W)\*(?!\s)(.+?)\*(?=\W|$)/g, "$1<i>$2</i>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");
  const out: string[] = [];
  let list: "ul" | "ol" | null = null;
  const close = () => { if (list) { out.push(`</${list}>`); list = null; } };
  for (const line of String(src || "").split(/\r?\n/)) {
    const b = line.match(/^\s*[-*•]\s+(.*)$/), n = line.match(/^\s*\d+[.)]\s+(.*)$/), h = line.match(/^#{1,4}\s+(.*)$/);
    if (b || n) {
      const want = b ? "ul" : "ol";
      if (list !== want) { close(); out.push(`<${want}>`); list = want; }
      out.push(`<li>${inline((b || n)![1])}</li>`);
    } else {
      close();
      if (h) out.push(`<p class="h">${inline(h[1])}</p>`);
      else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
    }
  }
  close();
  return out.join("");
}

export function AiAnswer({ run }: { run: AiRun }) {
  if (run.status === "unavailable") return <div className="zas-note info">{run.error || "AI isn't set up for this app yet."}</div>;
  if (run.status === "failed") return <div className="zas-note bad" role="alert">The AI couldn't finish: {run.error || "try again."}</div>;
  if (ACTIVE.has(run.status)) return <div className="zas-ai-think"><Loader /> Working on it…</div>;
  if (Array.isArray(run.result)) {
    return <div className="zas-ai-kvs">{run.result.map((f: any) => (
      <div key={f.key} className="zas-ai-kv"><span>{f.label}</span><div>{f.value == null || f.value === "" ? "—" : String(f.value)}</div></div>))}</div>;
  }
  return <div className="zas-ai-txt" dangerouslySetInnerHTML={{ __html: mdHTML(String(run.result ?? "")) }} />;
}

/** One suggestion: current → suggested per field, Use or Discard. */
export function AiSuggestionCard({ s, endpoint, onDone }: { s: AiSuggestion; endpoint: string; onDone: () => void }) {
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const act = async (use: boolean) => {
    setBusy(true);
    try {
      if (use) await api.aiAccept(endpoint, s.id); else await api.aiDiscard(endpoint, s.id);
      toast(use ? "Saved" : "Discarded");
      onDone();
    } catch (e: any) { toast("That didn't work", String(e?.message || e), true); } finally { setBusy(false); }
  };
  return (
    <div className="zas-ai-card" data-zas="ai-suggestion" data-zas-key={s.agent}>
      <div className="zas-ai-hd"><Sparkles /><span className="zas-ai-tag">AI suggestion</span><b>{s.name}</b></div>
      <div className="zas-ai-kvs">{s.fields.map((f) => (
        <div key={f.key} className="zas-ai-kv"><span>{f.label}</span>
          <div>{f.current != null && f.current !== "" && <s className="zas-ai-was">{String(f.current)}</s>}
            <b>{f.display == null || f.display === "" ? "—" : String(f.display)}</b></div></div>))}</div>
      <div className="zas-ai-ft">
        <Button size="sm" variant="primary" disabled={busy} onClick={() => act(true)}>Use</Button>
        <Button size="sm" disabled={busy} onClick={() => act(false)}>Discard</Button>
      </div>
    </div>
  );
}

/** The answer of a run that only shows (review: show, or no field to write): a dialog that waits for it. */
export function AiRunDialog({ title, endpoint, start, onClose, onDone }: {
  title: string; endpoint: string; start: () => Promise<AiRun>; onClose: () => void; onDone?: () => void;
}) {
  const [run, setRun] = useState<AiRun | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    start().then((r) => { setRun(r); return settle(endpoint, r, () => live.current); })
      .then((r) => { if (live.current) { setRun(r); if (r.applied || r.suggestion) onDone?.(); } })
      .catch((e) => live.current && setErr(String(e?.message || e)));
    return () => { live.current = false; };
  }, []);
  return (
    <Modal title={title} icon={<Sparkles />} iconTone="purple" wide onClose={onClose}
      footer={<Button onClick={onClose}>Close</Button>}>
      {err ? <div className="zas-note bad" role="alert">{err}</div>
        : !run ? <div className="zas-ai-think"><Loader /> Working on it…</div>
          : run.suggestion ? <AiSuggestionCard s={run.suggestion} endpoint={endpoint} onDone={() => { onDone?.(); onClose(); }} />
            : <>{run.applied && <div className="zas-note info">Saved to the record.</div>}<AiAnswer run={run} /></>}
    </Modal>
  );
}

type Msg = { who: "me" | "ai"; text: string; run?: AiRun };
/** "Ask AI": a conversation about one record (or the rows on screen) that the AI remembers. */
export function AiChatDialog({ click, endpoint, uuid, uuids, where, onClose }: {
  click: AiClick; endpoint: string; uuid?: string; uuids?: string[]; where?: string; onClose: () => void;
}) {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const session = useRef<string | null>(null);
  const send = async () => {
    const q = text.trim();
    if (!q || busy) return;
    setText(""); setBusy(true);
    setMsgs((m) => [...m, { who: "me", text: q }]);
    try {
      const r = await api.aiChat(endpoint, click.agent, q, { uuid, uuids, where, session: session.current });
      session.current = r.session_id || session.current;
      setMsgs((m) => [...m, { who: "ai", text: r.answer || "", run: r.run }]);
    } catch (e: any) {
      setMsgs((m) => [...m, { who: "ai", text: "", run: { status: "failed", error: String(e?.message || e) } as AiRun }]);
    } finally { setBusy(false); }
  };
  return (
    <Modal title={click.label} subtitle={click.name} icon={<MessageCircle />} iconTone="purple" wide onClose={onClose}
      footer={<div className="zas-ai-ask">
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask a question…" aria-label="Your question"
          onKeyDown={(e) => { if (e.key === "Enter") void send(); }} autoFocus />
        <Button variant="primary" icon={<Send />} onClick={send} disabled={busy || !text.trim()}>Ask</Button>
      </div>}>
      <div className="zas-ai-chat" data-zas="ai-chat">
        {!msgs.length && <div className="zas-ai-empty">Ask anything about {uuid ? "this record" : "these records"}. The AI sees only what this helper is allowed to read.</div>}
        {msgs.map((m, i) => m.who === "me"
          ? <div key={i} className="zas-ai-me">{m.text}</div>
          : <div key={i} className="zas-ai-bot">{m.run && m.run.status !== "done" ? <AiAnswer run={m.run} />
            : <div className="zas-ai-txt" dangerouslySetInnerHTML={{ __html: mdHTML(m.text) }} />}</div>)}
        {busy && <div className="zas-ai-think"><Loader /> Thinking…</div>}
      </div>
    </Modal>
  );
}

/** Opens what an AI click does: chat → the chat; button → run and show / suggest. */
export function openAiClick(c: AiClick, o: { endpoint: string; uuid?: string; uuids?: string[]; where: string;
  open: (n: React.ReactNode) => void; close: () => void; onDone?: () => void; }) {
  if (c.event === "chat") {
    return o.open(<AiChatDialog click={c} endpoint={o.endpoint} uuid={o.uuid} uuids={o.uuids} where={o.where} onClose={o.close} />);
  }
  o.open(<AiRunDialog title={c.label} endpoint={o.endpoint} onClose={o.close} onDone={o.onDone}
    start={() => api.aiRun(o.endpoint, c.agent, o.where, { uuid: o.uuid, uuids: o.uuids })} />);
}

/** What a record page shows under its header: open suggestions and runs still working (polled). */
export function AiRecordStrip({ endpoint, uuid, initial, onChanged }: {
  endpoint: string; uuid: string; initial?: api.RecordAi | null; onChanged: () => void;
}) {
  const [ai, setAi] = useState<api.RecordAi | null>(initial || null);
  useEffect(() => { setAi(initial || null); }, [initial]);
  useEffect(() => {
    if (!ai?.runs.some((r) => ACTIVE.has(r.status))) return;
    let live = true;
    Promise.all(ai.runs.filter((r) => ACTIVE.has(r.status)).map((r) => settle(endpoint, r, () => live)))
      .then(() => { if (live) return api.aiStatus(endpoint, uuid).then((x) => { if (live) { setAi(x); onChanged(); } }); })
      .catch(() => undefined);
    return () => { live = false; };
  }, [ai, endpoint, uuid]);
  if (!ai || (!ai.suggestions.length && !ai.runs.length)) return null;
  return (
    <div className="zas-ai-cards" data-zas="ai-strip">
      {ai.runs.map((r) => <div key={r.id} className="zas-ai-card slim"><div className="zas-ai-hd"><Sparkles /><b>{r.name}</b>
        <span className="zas-ai-think"><Loader /> Working on it…</span></div></div>)}
      {ai.suggestions.map((s) => <AiSuggestionCard key={s.id} s={s} endpoint={endpoint}
        onDone={() => api.aiStatus(endpoint, uuid).then((x) => { setAi(x); onChanged(); }).catch(() => onChanged())} />)}
    </div>
  );
}

/** A `type: ai` tab or 360 panel: the helper's latest answer for this record, and a button to run it. */
export function AiPanel({ agent, endpoint, uuid, title, onChanged }: { agent: string; endpoint: string; uuid: string; title?: string; onChanged?: () => void }) {
  const [run, setRun] = useState<AiRun | null>(null);
  const [busy, setBusy] = useState(false);
  const toast = useToast();
  const live = useRef(true);
  useEffect(() => () => { live.current = false; }, []);
  const go = async () => {
    setBusy(true);
    try {
      const r = await api.aiRun(endpoint, agent, "record", { uuid });
      setRun(r);
      const done = await settle(endpoint, r, () => live.current);
      if (live.current) { setRun(done); if (done.applied || done.suggestion) onChanged?.(); }
    } catch (e: any) { toast("The AI couldn't run", String(e?.message || e), true); } finally { setBusy(false); }
  };
  return (
    <div className="zas-ai-panel" data-zas="ai-panel" data-zas-key={agent}>
      <div className="zas-ai-hd"><Sparkles /><b>{title || "AI"}</b>
        <Button size="sm" icon={busy ? <Loader className="spin" /> : <Sparkles />} disabled={busy} onClick={go}>{run ? "Run again" : "Run"}</Button></div>
      {run ? (run.suggestion ? <AiSuggestionCard s={run.suggestion} endpoint={endpoint} onDone={() => { setRun(null); onChanged?.(); }} /> : <AiAnswer run={run} />)
        : <div className="zas-ai-empty">Run it to get an answer for this record.</div>}
    </div>
  );
}

/** In a create / edit form: "Fill from …" (form assist, from a document) and AI buttons that fill fields.
 * onFill gets {field: value}; FormDialog reloads the form with them for the person to check and save. */
export function AiFormBar({ endpoint, onFill }: { endpoint: string; onFill: (values: Record<string, any>) => void }) {
  const [clicks, setClicks] = useState<AiClick[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<{ bad?: boolean; text: string } | null>(null);
  const file = useRef<HTMLInputElement>(null);
  const pending = useRef<AiClick | null>(null);
  useEffect(() => {
    let live = true;
    api.aiClicks(endpoint, "form").then((c) => live && setClicks(c)).catch(() => undefined);
    return () => { live = false; };
  }, [endpoint]);
  if (!clicks.length) return null;
  const run = async (c: AiClick, files: File[]) => {
    setBusy(c.agent); setNote(null);
    try {
      const r = await api.aiForm(endpoint, c.agent, {}, files);
      if (r.run.status !== "done") setNote({ bad: r.run.status === "failed", text: r.run.error || "The AI couldn't fill the form." });
      else if (!Object.keys(r.values).length) setNote({ text: "The AI found nothing to fill in." });
      else {
        onFill(r.values);
        setNote({ text: `Filled ${Object.keys(r.values).length} field(s) with AI. Check them before saving` + (files.length ? "; attach the document below too." : ".") });
      }
    } catch (e: any) { setNote({ bad: true, text: String(e?.message || e) }); } finally { setBusy(null); }
  };
  return (
    <div className="zas-ai-formbar" data-zas="ai-form">
      {clicks.map((c) => (
        <Button key={c.agent + c.label} size="sm" icon={busy === c.agent ? <Loader className="spin" /> : <Sparkles />} disabled={!!busy}
          onClick={() => { if (c.event === "form_assist") { pending.current = c; file.current?.click(); } else void run(c, []); }}>{c.label}</Button>
      ))}
      <input ref={file} type="file" hidden accept=".pdf,image/*" onChange={(e) => {
        const f = Array.from(e.target.files || []); e.target.value = "";
        if (pending.current && f.length) void run(pending.current, f);
      }} />
      {note && <div className={`zas-note ${note.bad ? "bad" : "info"}`}>{note.text}</div>}
    </div>
  );
}

/** Row-menu items and list-header buttons for the React list (ZasTable) from the table metadata. */
export function aiMenuItems(clicks: AiClick[] | undefined, run: (c: AiClick) => void) {
  return (clicks || []).map((c) => ({ key: "ai:" + c.agent + ":" + c.label, label: c.label, group: "AI", icon: <Sparkles />, onClick: () => run(c) }));
}
