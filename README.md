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

1. Clone the repository:
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

2. Prepare Your Server 

    SSH into your server:

        ssh youruser@your.server.ip

    Update and install dependencies:
        sudo apt update
        sudo apt install python3 python3-pip python3-venv nginx

3. Set Up Your Application

    Clone your repository:
        git clone https://github.com/yourusername/secure-share.git
        cd secure-share

    Create and activate a virtual environment:
        python3 -m venv venv
        source venv/bin/activate

    Install the required packages:
        pip install -r requirements.txt
    Or, if not using a requirements file:
        pip install flask gunicorn

4. Test with Gunicorn
    Run Gunicorn to verify your app:
        gunicorn app:app --bind 0.0.0.0:8000
        Now, visit http://your.server.ip:8000 to see your app running.

5. Create a systemd Service for Gunicorn
    Create a service file so your app runs in the background.

    Create the service file:
        sudo nano /etc/systemd/system/secure-share.service

    Add the following (adjust paths and username):

        [Unit]
        Description=Gunicorn instance to serve Secure Share
        After=network.target

        [Service]
        User=youruser
        Group=www-data
        WorkingDirectory=/home/youruser/secure-share
        Environment="PATH=/home/youruser/secure-share/venv/bin"
        ExecStart=/home/youruser/secure-share/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app

        [Install]
        WantedBy=multi-user.target
        Reload systemd and start the service:

    sudo systemctl daemon-reload
    sudo systemctl start secure-share
    sudo systemctl enable secure-share

    Check the service status:
    sudo systemctl status secure-share

6. Configure Nginx as a Reverse Proxy

    Create an Nginx configuration file:
    sudo nano /etc/nginx/sites-available/secure-share
    Insert the following configuration (update server_name as needed):
        server {
            listen 80;
            server_name your.server.ip;  # or your domain name

            location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }

    Enable the site and reload Nginx:
        sudo ln -s /etc/nginx/sites-available/secure-share /etc/nginx/sites-enabled
        sudo nginx -t
        sudo systemctl reload nginx

7. (Optional) Set Up SSL with Let’s Encrypt
    For production environments, secure your site with SSL:
        sudo apt install certbot python3-certbot-nginx
        sudo certbot --nginx -d your.domain.com
