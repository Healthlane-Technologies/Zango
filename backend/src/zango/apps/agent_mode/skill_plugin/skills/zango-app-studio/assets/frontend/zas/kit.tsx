// The app's kit: each piece is the app's own (src/custom/kit/index.ts) when it exports one under the
// same name, else the default kit's. Free design builds those pieces from the approved prototype
// (references/open-mode.md, "The kit"), so every runtime page (list, 360, drawer, dialogs) draws with
// them and no screen has to be rebuilt to match the prototype. Default design leaves the folder empty.
//
// Resolved at render time, never at import: src/custom/kit wraps the base pieces from "../../zas/ui",
// "../../zas/ZasTable" and "../../zas/Shell", and those import this file back.
import React from "react";
import * as BASE from "./ui";
import { ZasTable as BaseZasTable } from "./ZasTable";
import { makeShell as baseMakeShell } from "./Shell";
import type { ShellOptions } from "./Shell";
import * as CUSTOM from "../custom/kit";

const APP = CUSTOM as Record<string, any>;

// The pieces an app may restyle. Keep in step with zas_test/design.py KIT_PIECES.
export const KIT_PIECES = [
  "Button", "Badge", "Chip", "Panel", "StatTile", "Tabs", "Timeline", "FieldGrid", "Drawer", "Modal",
  "EmptyState", "Banner", "Kpis", "Bars", "List", "MiniTable", "Board", "Progress", "ZasTable", "makeShell",
] as const;

function piece<T extends React.ComponentType<any>>(name: string, base: T): T {
  const Piece = (props: any) => {
    const C = (APP[name] as T | undefined) || base;
    return <C {...props} />;
  };
  Piece.displayName = `Kit(${name})`;
  return Piece as unknown as T;
}

/** Which pieces the app overrides (the gallery's mockup-kit mode lists them). */
export const appPieces = (): string[] => KIT_PIECES.filter((n) => typeof APP[n] === "function");

export const Button = piece("Button", BASE.Button);
export const Badge = piece("Badge", BASE.Badge);
export const Chip = piece("Chip", BASE.Chip);
export const Panel = piece("Panel", BASE.Panel);
export const StatTile = piece("StatTile", BASE.StatTile);
export const Tabs = piece("Tabs", BASE.Tabs);
export const Timeline = piece("Timeline", BASE.Timeline);
export const FieldGrid = piece("FieldGrid", BASE.FieldGrid);
export const Drawer = piece("Drawer", BASE.Drawer);
export const Modal = piece("Modal", BASE.Modal);
export const EmptyState = piece("EmptyState", BASE.EmptyState);
export const Banner = piece("Banner", BASE.Banner);
export const Kpis = piece("Kpis", BASE.Kpis);
export const Bars = piece("Bars", BASE.Bars);
export const List = piece("List", BASE.List) as typeof BASE.List;
export const MiniTable = piece("MiniTable", BASE.MiniTable) as typeof BASE.MiniTable;
export const Board = piece("Board", BASE.Board);
export const Progress = piece("Progress", BASE.Progress);
export const ZasTable = piece("ZasTable", BaseZasTable);

export function makeShell(options: ShellOptions = {}) {
  return ((APP.makeShell as typeof baseMakeShell | undefined) || baseMakeShell)(options);
}
