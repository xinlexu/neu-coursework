// server.js

// Built-in Node modules we need
const http = require('http');  // To create an HTTP server
const fs = require('fs');      // To read files from disk
const path = require('path');  // To safely join file paths
const url = require('url');    // To parse the incoming request URL

// A simple MIME type lookup table.
// Key = file extension, Value = correct Content-Type header.
// The browser uses Content-Type to decide how to interpret the bytes.
// e.g. .css must be 'text/css' so the browser applies it as a stylesheet.
const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.ico':  'image/x-icon',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.svg':  'image/svg+xml'
};

// Create the HTTP server
http.createServer((req, res) => {
  // Parse the requested URL to get the pathname (/index.html, /style.css, etc.)
  const parsed = url.parse(req.url);

  // Convert URL path into an absolute file path on disk
  let pathname = path.join(process.cwd(), decodeURIComponent(parsed.pathname));

  // If the request path is a directory, default to index.html inside it
  if (fs.existsSync(pathname) && fs.statSync(pathname).isDirectory()) {
    pathname = path.join(pathname, 'index.html');
  }

  // If the request path is exactly '/', serve index.html from the current folder
  if (parsed.pathname === '/') {
    pathname = path.join(process.cwd(), 'index.html');
  }

  // Read the file from disk asynchronously
  fs.readFile(pathname, (err, data) => {
    if (err) {
      // If not found or error reading, return 404 with error message
      res.writeHead(404, {'Content-Type': 'text/plain; charset=utf-8'});
      return res.end(`error: ${err.message}\n${err.stack}`);
    }

    // Determine the file extension to pick the correct MIME type
    const ext = path.extname(pathname).toLowerCase();

    // Write the HTTP header with appropriate Content-Type (defaults to binary if unknown)
    res.writeHead(200, {'Content-Type': mime[ext] || 'application/octet-stream'});

    // Send the file contents to the browser
    res.end(data);
  });

// Start listening on port 5500
}).listen(5500, () => {
  console.log('Serving on http://localhost:5500');
});
