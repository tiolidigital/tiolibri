// Bramka G1-G4: odpalenie PRAWDZIWEGO segmentuj() z FABRYKA-redaktor (galaz redaktor)
// na NASZYM wyjsciu .md. Zero reimplementacji po stronie TIOLIBRI.
import { readFileSync, writeFileSync } from "node:fs";
import { segmentuj } from "/Users/piotrmichalski/Documents/SaaS_Factory2026/FABRYKA-redaktor/src/redaktor/chunker/segmentuj.ts";

const [mdPath, outPath] = process.argv.slice(2);
const md = readFileSync(mdPath, "utf8");
const bloki = segmentuj(md);

// chunks.json — ksztalt konsumenta: typ + tekst + offset
writeFileSync(outPath, JSON.stringify(bloki, null, 2), "utf8");
console.error(`chunks: ${bloki.length} -> ${outPath}`);
