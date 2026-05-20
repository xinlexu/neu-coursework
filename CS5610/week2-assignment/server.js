const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

const server = http.createServer((req, res) => {
  let filePath = '';

  if (req.url === '/' || req.url === '/Hello_world.html') {
    filePath = path.join(__dirname, 'Hello_world.html');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  } else if (req.url === '/style.css') {
    filePath = path.join(__dirname, 'style.css');
    res.writeHead(200, { 'Content-Type': 'text/css; charset=utf-8' });
  } else {
    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    return res.end('404 Not Found');
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('SERVER ERROR!');
    }
    res.end(data);
  });
});

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
