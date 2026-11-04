// Reuse frozen compiler, deployments, local EDR and transaction capture.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const lock = JSON.parse(fs.readFileSync(path.join(root,'conformance/erc8004-role-policy-v2/source-lock.json')));
for (const [name,digest] of Object.entries(lock.reused_files)) {
  if (sha(fs.readFileSync(path.join(root,name))) !== digest) throw Error('reused source drift: ' + name);
}
const implementationLock = JSON.parse(fs.readFileSync(path.join(root,lock.implementation_lock)));
for (const [name,digest] of Object.entries(implementationLock.implementation.files)) {
  if (sha(fs.readFileSync(path.join(process.argv[2],name))) !== digest) throw Error('implementation pin drift: ' + name);
}
const original = fs.readFileSync(path.join(root,'tools/erc8004/evm.mjs'),'utf8');
const start = original.indexOf('for (const test of request.cases) {');
const end = original.indexOf('const output={observations,runtime:');
if (start < 0 || end <= start) throw Error('frozen composition bounds');
const prefix = original.slice(0,start).replace("const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');",`const root = ${JSON.stringify(root)};`);
const body = fs.readFileSync(path.join(root,'tools/erc8004_role_policy_v2/scenarios.mjs'));
if (sha(body) !== lock.scenarios_sha256) throw Error('scenario composition pin drift');
await import('data:text/javascript;base64,' + Buffer.from(prefix + body.toString('utf8') + '\n' + original.slice(end)).toString('base64'));
