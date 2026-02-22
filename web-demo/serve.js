/**
 * SmartPhoto Web Demo - Static file server (zero dependencies)
 * Usage: node serve.js [port]
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = parseInt(process.argv[2], 10) || 3000;

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

const ROOT = __dirname;

const server = http.createServer((req, res) => {
  let urlPath = new URL(req.url, `http://localhost:${PORT}`).pathname;
  if (urlPath === '/') urlPath = '/index.html';

  const filePath = path.join(ROOT, urlPath);
  const safePath = path.resolve(filePath);
  if (!safePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(safePath, (err, data) => {
    if (err) {
      if (err.code === 'ENOENT') {
        // SPA fallback: serve index.html for non-file routes
        fs.readFile(path.join(ROOT, 'index.html'), (err2, html) => {
          if (err2) {
            res.writeHead(500);
            res.end('Server Error');
            return;
          }
          res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
          res.end(html);
        });
      } else {
        res.writeHead(500);
        res.end('Server Error');
      }
      return;
    }

    const ext = path.extname(safePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';

    res.writeHead(200, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache',
      'Access-Control-Allow-Origin': '*',
    });
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`\n  SmartPhoto Web Demo`);
  console.log(`  -------------------`);
  console.log(`  Local:   http://localhost:${PORT}`);
  console.log(`  Network: http://0.0.0.0:${PORT}\n`);
  console.log(`  Make sure the backend is running at http://localhost:8000\n`);
});
