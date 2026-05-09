const fs = require('fs');
const path = '/home/charles/.odin/memory.json'; // adjust path

let memories = [];
try { memories = JSON.parse(fs.readFileSync(path, 'utf8')); } catch {}

memories.push({
  id: Date.now(),
  tag: $input.first().json.body.tag,
  content: $input.first().json.body.content,
  timestamp: new Date().toISOString()
});

fs.writeFileSync(path, JSON.stringify(memories, null, 2));
return [{ json: { status: 'saved', count: memories.length } }];


const fs = require('fs');
const path = '/home/charles/.odin/memory.json';
const tag = $input.first().json.body.tag;

let memories = [];
try { memories = JSON.parse(fs.readFileSync(path, 'utf8')); } catch {}

const results = tag
  ? memories.filter(m => m.tag === tag)
  : memories.slice(-20); // last 20 if no tag

return [{ json: { memories: results } }];



const fs = require('fs');
const path = '/home/charles/.odin/memory.json';
const cutoff = Date.now() - (7 * 24 * 60 * 60 * 1000); // 7 days

let memories = [];
try { memories = JSON.parse(fs.readFileSync(path, 'utf8')); } catch {}

const kept = memories.filter(m => new Date(m.timestamp).getTime() > cutoff);
fs.writeFileSync(path, JSON.stringify(kept, null, 2));

return [{ json: { pruned: memories.length - kept.length, remaining: kept.length } }];


Response body: {{ $json }}


POST http://localhost:5678/webhook/odin-memory
{ "action": "write", "tag": "project", "content": "ODIN_PRO bridge is on port 8099" }



{ "action": "read", "tag": "project" }



{ "action": "prune" }