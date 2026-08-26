import type { PropsWithChildren } from "react";

export function Panel({ children }: PropsWithChildren) {
  return <section className="rounded-lg border p-4">{children}</section>;
}

export type { PropsWithChildren } from "react";
