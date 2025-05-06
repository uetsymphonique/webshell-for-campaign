# webshell-for-campaign

## Nginx Setup
```bash
// /usr/local/nginx/conf/nginx.conf
worker_processes  1;

events {
    worker_connections  1024;
}

http {
    include       mime.types;
    default_type  application/octet-stream;

    sendfile        on;
    keepalive_timeout  65;

    server {
        listen       80;
        server_name  localhost;

        location / {
            root   /usr/local/nginx/html;
            index  index.html index.htm;
        }

        location /shell/ {
            proxy_pass http://127.0.0.1:3000/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            client_max_body_size 5M;
        }

        error_page  500 502 503 504 /50x.html;
        location = /50x.html {
            root   /usr/local/nginx/html;
        }
    }
}

pid /usr/local/nginx/logs/nginx.pid;
```
