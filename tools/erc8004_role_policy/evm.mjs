// Reuse the exact pinned v0 compiler/deployment/runtime and receipt capture.
// Only the scenario loop is replaced; historical source bytes remain frozen.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const original = fs.readFileSync(path.join(root, 'tools/erc8004/evm.mjs'));
if (crypto.createHash('sha256').update(original).digest('hex') !== '995e957138979c936a29d1251c357a3ca2e8d8a09b46aa48ab2dec7221be1193') throw Error('frozen EVM runner drift');
const source = original.toString('utf8');
const start = source.indexOf('for (const test of request.cases) {');
const end = source.indexOf('const output={observations,runtime:');
if (start < 0 || end <= start) throw Error('runner composition bounds');
const prefix = source.slice(0, start).replace("const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');", `const root = ${JSON.stringify(root)};`);
const body = fs.readFileSync(path.join(root, 'tools/erc8004_role_policy/scenarios.mjs'), 'utf8');
await import('data:text/javascript;base64,' + Buffer.from(prefix + body + '\n' + source.slice(end)).toString('base64'));
