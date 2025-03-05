# Secure Share

Secure Share is a secure, one-time file-sharing web application built with Flask. Files are encrypted in the browser and stored on the server in an obfuscated manner. The encrypted download URL includes a client-side encryption key (as a URL fragment) so that only the intended recipient can decrypt the file. After one download, the file is removed from the server.

## Features

- **Client-side encryption:** Files are encrypted in the user's browser using AES-GCM before upload.
- **Encrypted filename:** The original filename is encrypted on the client side so that it is never stored in plaintext on the server.
- **One-time download:** Each file can be downloaded only once.
- **Short URLs:** Uses a short token (generated via Python's `secrets` module) in the download URL.
- **Modern UI:** Built with Bootstrap, Font Awesome, and Google Fonts for a polished, responsive user experience.
- **Copy Link Button:** Users can easily copy the generated download URL using the Async Clipboard API (with a fallback to `document.execCommand`).
- **Help Page:** Provides instructions on how to use the application.

## Local Setup

### Prerequisites

- Python 3.6+
- pip
- Virtualenv (optional but recommended)

### Installation

    Clone the repository:
        git clone https://github.com/eazarkman/secure-share.git
        cd secure-share

    Create and activate a virtual environment:
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

    Or install Flask and Gunicorn manually:
        pip install flask gunicorn

    Run the application locally:

        python app.py
        Open your browser and visit http://127.0.0.1:5000/ to test the app.


    Deployment on a Bare-Bones Linux Server
    Below are step-by-step instructions for deploying Secure Share on an Ubuntu/Debian server using Gunicorn and Nginx.

