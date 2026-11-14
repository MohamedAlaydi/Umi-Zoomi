// Tiny static server for this folder, so the frames can be opened over http://localhost.
// Run: node serve.mjs   (then open http://localhost:8791/)
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.argv[2] || process.env.PORT || 8791);
const types = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.png': 'image/png', '.json': 'application/json', '.md': 'text/plain; charset=utf-8', '.svg': 'image/svg+xml' };

http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  const file = path.normalize(path.join(root, url));
  if (!file.startsWith(root)) { res.writeHead(403); res.end('no'); return; }
  if (url === '/') {
    const list = fs.readdirSync(root).filter(f => f.endsWith('.html')).sort();
    res.writeHead(200, { 'content-type': types['.html'] });
    res.end('<meta charset="utf-8"><title>pitch-design</title><body style="font:20px/1.6 system-ui;padding:40px">' +
      list.map(f => `<a href="/${f}">${f}</a>`).join('<br>'));
    return;
  }
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end('not found'); return; }
    res.writeHead(200, { 'content-type': types[path.extname(file)] || 'application/octet-stream', 'cache-control': 'no-store' });
    res.end(data);
  });
}).listen(port, () => console.log('pitch-design on http://localhost:' + port));
