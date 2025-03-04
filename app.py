from flask import Flask, request, render_template_string, send_file, url_for
import os
import uuid

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 * 1024  # 256 MB

# In-memory storage for file metadata.
# We store only the encrypted filename (not the plain name), the file path, and a download flag.
files_data = {}

# Ensure the uploads directory exists.
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

###############################################################################
# 1) SHARED NAVBAR & HELPER HTML
###############################################################################
NAVBAR_HTML = """
<nav class="navbar navbar-expand-lg navbar-light">
  <a class="navbar-brand" href="/" style="color: #fff; font-weight: 600;">
    <i class="fas fa-shield-alt"></i> Secure Share
  </a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarToggler" 
          aria-controls="navbarToggler" aria-expanded="false" aria-label="Toggle navigation">
    <span class="navbar-toggler-icon" style="color: #fff;"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarToggler">
    <ul class="navbar-nav ml-auto">
      <li class="nav-item">
        <a class="nav-link" href="/" style="color: #fff;">Home</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="/help" style="color: #fff;">Help</a>
      </li>
    </ul>
  </div>
</nav>
"""

###############################################################################
# 2) UPLOAD (HOME) PAGE
###############################################################################
INDEX_HTML = """
<!doctype html>
<html>
<head>
  <title>Secure Share - Upload</title>
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <!-- Font Awesome for icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #ffffff 0%, #f2f2f2 100%);
      font-family: 'Poppins', sans-serif;
    }
    /* Navbar styling */
    .navbar {
      background: linear-gradient(45deg, #3b5998, #8b9dc3);
    }
    .navbar-toggler {
      border-color: rgba(255,255,255,0.1);
    }
    .navbar-toggler-icon {
      background-image: url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 30 30' " +
        "xmlns='http://www.w3.org/2000/svg'%3E%3Cpath stroke='rgba(255, 255, 255, 0.8)' " +
        "stroke-width='2' stroke-linecap='round' stroke-miterlimit='10' d='M4 7h22M4 15h22M4 23h22' " +
        "/%3E%3C/svg%3E");
    }

    /* Card styling */
    .card {
      max-width: 600px; 
      margin: 40px auto;
      border-radius: 8px;
      box-shadow: 0 0 20px rgba(0,0,0,0.05);
    }
    .card-header {
      border-top-left-radius: 8px;
      border-top-right-radius: 8px;
      background: #3b5998;
      color: #fff;
      font-weight: 600;
    }

    /* Buttons & progress bar */
    .btn-success {
      background: linear-gradient(45deg, #4CAF50, #81C784);
      border: none;
      color: #fff;
    }
    .btn-success:hover {
      background: linear-gradient(45deg, #388E3C, #66BB6A);
      color: #fff;
    }
    #progressBar {
      transition: width 0.4s ease;
    }

    /* Footer */
    footer {
      text-align: center;
      margin: 40px 0 20px;
      color: #999;
    }
  </style>
</head>
<body>
""" + NAVBAR_HTML + """
  <div class="container">
    <div class="card shadow-sm">
      <div class="card-header">
        <h4 class="mb-0"><i class="fas fa-lock"></i> Secure File Upload</h4>
      </div>
      <div class="card-body">
        <form id="uploadForm">
          <div class="form-group">
            <label for="fileInput">Select a file (max 256 MB):</label>
            <input type="file" class="form-control-file" id="fileInput" required>
          </div>
          <button type="submit" class="btn btn-success">
            <i class="fas fa-cloud-upload-alt"></i> Encrypt & Upload
          </button>
        </form>

        <div id="progressContainer" class="mt-3" style="display:none;">
          <div class="progress">
            <div id="progressBar" class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%"></div>
          </div>
          <small id="progressText" class="form-text text-muted"></small>
        </div>

        <div id="result" class="mt-4"></div>
      </div>
    </div>
  </div>

  <!-- Bootstrap JS (for responsive navbar toggling) -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

<script>
// Utility: Convert ArrayBuffer to hex string.
function buf2hex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map(b => ('00' + b.toString(16)).slice(-2))
    .join('');
}

// Encrypt the file content using AES-GCM.
async function encryptFile(file) {
    // Generate a random AES-256 key.
    const key = await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
    // Export the key as a hex string.
    const rawKey = await window.crypto.subtle.exportKey("raw", key);
    const keyHex = buf2hex(rawKey);
    
    // Generate a random 12-byte IV.
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    
    // Read the file as an ArrayBuffer.
    const arrayBuffer = await file.arrayBuffer();
    
    // Encrypt the file content.
    const encryptedContent = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        arrayBuffer
    );
    
    // Concatenate the IV and the encrypted content.
    const encryptedBlob = new Blob([iv, new Uint8Array(encryptedContent)]);
    
    return { encryptedBlob, keyHex, keyObj: key };
}

// Encrypt the filename using the same key (with a separate IV).
async function encryptFilename(filename, key) {
    const encoder = new TextEncoder();
    const filenameBytes = encoder.encode(filename);
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const encryptedBuffer = await window.crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        key,
        filenameBytes
    );
    const ivHex = buf2hex(iv);
    const cipherHex = buf2hex(encryptedBuffer);
    return ivHex + ":" + cipherHex;
}

document.getElementById("uploadForm").addEventListener("submit", async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) {
        alert("Please select a file.");
        return;
    }
    const file = fileInput.files[0];

    // Show progress indicator.
    document.getElementById("progressContainer").style.display = "block";
    document.getElementById("progressText").innerText = "Encrypting file...";
    document.getElementById("progressBar").style.width = "20%";
    
    // Encrypt file content.
    const { encryptedBlob, keyHex, keyObj } = await encryptFile(file);
    
    // Encrypt the filename.
    const encryptedFilename = await encryptFilename(file.name, keyObj);
    
    // Update progress.
    document.getElementById("progressText").innerText = "Uploading file...";
    document.getElementById("progressBar").style.width = "50%";
    
    // Prepare form data.
    const formData = new FormData();
    formData.append("file", encryptedBlob, file.name);
    formData.append("encrypted_filename", encryptedFilename);
    
    // Upload the encrypted file and encrypted filename to the server.
    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });
    const resultText = await response.text();
    
    // Finalize progress.
    document.getElementById("progressBar").style.width = "100%";
    document.getElementById("progressText").innerText = "Upload complete!";
    
    // Replace placeholder with the actual encryption key in the URL fragment.
    const resultContainer = document.getElementById("result");
    const finalHtml = resultText.replace("YOUR_ENCRYPTION_KEY", keyHex);
    resultContainer.innerHTML = finalHtml;
});
</script>

<footer>
  <small>© 2025 Secure Share. All rights reserved.</small>
</footer>
</body>
</html>
"""

###############################################################################
# 3) DOWNLOAD PAGE
###############################################################################
DOWNLOAD_HTML = """
<!doctype html>
<html>
<head>
  <title>Secure Share - Download</title>
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <!-- Font Awesome for icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #ffffff 0%, #f2f2f2 100%);
      font-family: 'Poppins', sans-serif;
    }
    .navbar {
      background: linear-gradient(45deg, #3b5998, #8b9dc3);
    }
    .navbar-toggler {
      border-color: rgba(255,255,255,0.1);
    }
    .navbar-toggler-icon {
      background-image: url("data:image/svg+xml;charset=utf8,%3Csvg viewBox='0 0 30 30' " +
        "xmlns='http://www.w3.org/2000/svg'%3E%3Cpath stroke='rgba(255, 255, 255, 0.8)' " +
        "stroke-width='2' stroke-linecap='round' stroke-miterlimit='10' d='M4 7h22M4 15h22M4 23h22' " +
        "/%3E%3C/svg%3E");
    }
    .card {
      max-width: 600px; 
      margin: 40px auto;
      border-radius: 8px;
      box-shadow: 0 0 20px rgba(0,0,0,0.05);
    }
    .card-header {
      border-top-left-radius: 8px;
      border-top-right-radius: 8px;
      background: #6c757d;
      color: #fff;
      font-weight: 600;
    }
    footer {
      text-align: center;
      margin: 40px 0 20px;
      color: #999;
    }
  </style>
</head>
<body>
""" + NAVBAR_HTML + """
  <div class="container">
    <div class="card shadow-sm">
      <div class="card-header">
        <h4 class="mb-0"><i class="fas fa-file-download"></i> Decrypt & Download File</h4>
      </div>
      <div class="card-body">
        <p id="status" class="mb-0">Preparing your download...</p>
        <a href="/" class="btn btn-link mt-3">← Return Home</a>
      </div>
    </div>
  </div>

  <!-- Bootstrap JS -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

<script>
function hexToBytes(hex) {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  }
  return bytes;
}

async function decryptFilename(encryptedStr, cryptoKey) {
  const parts = encryptedStr.split(":");
  if (parts.length !== 2) throw new Error("Invalid encrypted filename format");
  const iv = hexToBytes(parts[0]);
  const cipherBytes = hexToBytes(parts[1]);
  const decryptedBuffer = await crypto.subtle.decrypt(
     { name: "AES-GCM", iv: iv },
     cryptoKey,
     cipherBytes
  );
  const decoder = new TextDecoder();
  return decoder.decode(decryptedBuffer);
}

async function downloadAndDecrypt() {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const keyHex = params.get('key');
    if (!keyHex) {
        document.getElementById("status").innerText = 'Error: No encryption key provided in URL.';
        return;
    }
    
    // Remove the key from the URL for security
    window.history.replaceState(null, '', window.location.pathname);
    
    const pathParts = window.location.pathname.split('/');
    const fileId = pathParts[pathParts.length - 1];
    
    // Import the encryption key
    const keyBytes = hexToBytes(keyHex);
    const cryptoKey = await crypto.subtle.importKey(
        'raw',
        keyBytes,
        { name: 'AES-GCM' },
        false,
        ['decrypt']
    );
    
    // This placeholder will be replaced in the route handler:
    const encryptedFilename = "__ENCRYPTED_FILENAME__";
    let decryptedFilename;
    try {
        decryptedFilename = await decryptFilename(encryptedFilename, cryptoKey);
    } catch (e) {
        document.getElementById("status").innerText = 'Error decrypting filename: ' + e;
        return;
    }
    
    // Fetch the encrypted file
    const response = await fetch('/file/' + fileId);
    if (!response.ok) {
        document.getElementById("status").innerText = 'Error: Could not fetch file from server.';
        return;
    }
    const encryptedArrayBuffer = await response.arrayBuffer();
    
    // The file structure is: [12-byte IV][ciphertext]
    const iv = encryptedArrayBuffer.slice(0, 12);
    const ciphertext = encryptedArrayBuffer.slice(12);
    
    try {
        const decryptedBuffer = await crypto.subtle.decrypt(
            { name: 'AES-GCM', iv: new Uint8Array(iv) },
            cryptoKey,
            ciphertext
        );
        
        const decryptedBlob = new Blob([decryptedBuffer]);
        const downloadUrl = URL.createObjectURL(decryptedBlob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = decryptedFilename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        document.getElementById("status").innerText = 'Download started.';
    } catch (e) {
        document.getElementById("status").innerText = 'Error during decryption: ' + e;
    }
}

downloadAndDecrypt();
</script>

<footer>
  <small>© 2025 Secure Share. All rights reserved.</small>
</footer>
</body>
</html>
"""

###############################################################################
# 4) HELP PAGE
###############################################################################
HELP_HTML = """
<!doctype html>
<html>
<head>
  <title>Secure Share - Help</title>
  <!-- Bootstrap CSS -->
  <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
  <!-- Font Awesome for icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.gstatic.com">
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap" rel="stylesheet">
  <style>
    body {
      margin: 0;
      padding: 0;
      background: linear-gradient(135deg, #ffffff 0%, #f2f2f2 100%);
      font-family: 'Poppins', sans-serif;
    }
    .navbar {
      background: linear-gradient(45deg, #3b5998, #8b9dc3);
    }
    .card {
      max-width: 600px; 
      margin: 40px auto;
      border-radius: 8px;
      box-shadow: 0 0 20px rgba(0,0,0,0.05);
    }
    .card-header {
      border-top-left-radius: 8px;
      border-top-right-radius: 8px;
      background: #17a2b8;
      color: #fff;
      font-weight: 600;
    }
    footer {
      text-align: center;
      margin: 40px 0 20px;
      color: #999;
    }
  </style>
</head>
<body>
""" + NAVBAR_HTML + """
  <div class="container">
    <div class="card shadow-sm">
      <div class="card-header">
        <h4 class="mb-0"><i class="fas fa-question-circle"></i> Help & Tips</h4>
      </div>
      <div class="card-body">
        <h5>How to Use Secure Share</h5>
        <ol>
          <li>Go to the Home page and upload your file. The file is encrypted in your browser.</li>
          <li>Copy the generated download URL (with the encryption key fragment).</li>
          <li>Share that URL with the intended recipient.</li>
          <li>The recipient opens the link, decrypts the file in their browser, and downloads it.</li>
        </ol>
        <p class="mt-3">
          Your file is removed from our server as soon as it’s downloaded (one-time download). 
          The original filename is never stored in plaintext on our servers.
        </p>
        <a href="/" class="btn btn-primary mt-3"><i class="fas fa-home"></i> Back to Home</a>
      </div>
    </div>
  </div>

  <!-- Bootstrap JS -->
  <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/js/bootstrap.bundle.min.js"></script>

<footer>
  <small>© 2025 Secure Share. All rights reserved.</small>
</footer>
</body>
</html>
"""

###############################################################################
# 5) ROUTES & LOGIC
###############################################################################
@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/help')
def help_page():
    return render_template_string(HELP_HTML)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "Missing file", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # Generate a unique file identifier
    file_id = str(uuid.uuid4())
    random_filename = file_id + ".enc"  # Obfuscate the file on disk
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], random_filename)
    file.save(file_path)
    
    encrypted_filename = request.form.get('encrypted_filename')
    if not encrypted_filename:
        return "Missing encrypted filename", 400
    
    files_data[file_id] = {
        'encrypted_filename': encrypted_filename,
        'filepath': file_path,
        'downloaded': False
    }
    
    download_url = request.url_root.rstrip("/") + url_for("download_page", file_id=file_id)
    
    # Use the Async Clipboard API fallback approach
    # We do NOT use an f-string for the large HTML block, but a normal string + .format()
    copy_js = """
<script>
async function copyLink() {
  const linkElement = document.getElementById('downloadURL');
  const linkText = linkElement.value;
  
  if (navigator.clipboard && window.isSecureContext) {
    // Modern Async Clipboard API
    try {
      await navigator.clipboard.writeText(linkText);
      alert("Download link copied to clipboard!");
    } catch (e) {
      console.error(e);
      alert("Unable to copy link. Please copy manually.");
    }
  } else {
    // Fallback for older browsers
    linkElement.select();
    linkElement.setSelectionRange(0, 99999);
    try {
      document.execCommand('copy');
      alert("Download link copied to clipboard!");
    } catch (e) {
      console.error(e);
      alert("Unable to copy link. Please copy manually.");
    }
  }
}
</script>
"""

    # Build the HTML response with .format() for the download URL
    message = (
        "<h2>File Uploaded Successfully!</h2>"
        "<p>Download URL (one-time use):</p>"
        "<div class='input-group mb-3'>"
        f"<input type='text' id='downloadURL' class='form-control' value='{download_url}#key=YOUR_ENCRYPTION_KEY' readonly>"
        "<div class='input-group-append'>"
        "<button class='btn btn-outline-secondary' type='button' onclick='copyLink()'>"
        "<i class='fas fa-copy'></i> Copy Link"
        "</button>"
        "</div>"
        "</div>"
        + copy_js
    )
    return message

@app.route('/download/<file_id>')
def download_page(file_id):
    if file_id not in files_data:
        return "File not found or already downloaded.", 404
    
    # Insert the encrypted filename into the download HTML
    page_html = DOWNLOAD_HTML.replace("__ENCRYPTED_FILENAME__", files_data[file_id]['encrypted_filename'])
    return render_template_string(page_html)

@app.route('/file/<file_id>')
def serve_file(file_id):
    file_info = files_data.get(file_id)
    if not file_info:
        return "File not found or already downloaded.", 404
    if file_info.get('downloaded'):
        return "File already downloaded.", 404
    
    file_info['downloaded'] = True
    file_path = file_info['filepath']
    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True, download_name="encrypted_file")
        os.remove(file_path)
        del files_data[file_id]
        return response
    else:
        return "File not found on server.", 404

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

