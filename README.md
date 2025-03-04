# secure-share
Secure Share is a secure, one-time file-sharing web application built with Flask. Files are encrypted in the browser using AES-GCM before upload, and the download URL includes the decryption key (as a URL fragment). Each file can be downloaded only once, after which it is removed from the server.
