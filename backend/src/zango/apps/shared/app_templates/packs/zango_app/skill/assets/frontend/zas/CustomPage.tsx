// A spec page of type custom: the page shell (title, design tokens, toasts) around the
// slot the agent writes in src/custom/slots/<Component>.tsx.
import React from "react";
import * as api from "./api";
import { SPEC } from "./config";
import * as SLOTS from "../custom/slots";
import { EmptyState, ToastHost } from "./ui";

const pages: Record<string, React.FC> = {};

export function makeCustomPage(pageCode: string): React.FC {
  if (pages[pageCode]) return pages[pageCode];
  const page = SPEC.pages[pageCode];
  const slotName = page?.export;
  const C: React.FC = () => {
    const Slot = slotName ? (SLOTS as Record<string, React.ComponentType<any>>)[slotName] : undefined;
    return (
      <ToastHost>
        <div className="zas zas-page" data-zas="page" data-zas-key={pageCode}>
          <div className="zas-ph"><div><h1>{page?.title}</h1></div></div>
          {Slot ? <Slot api={api} /> : <EmptyState title="This page is not built yet" text={`Add ${slotName} to src/custom/slots.`} zasKey={pageCode} />}
        </div>
      </ToastHost>
    );
  };
  C.displayName = `Page_${pageCode}`;
  pages[pageCode] = C;
  return C;
}
