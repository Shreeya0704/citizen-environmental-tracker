FROM nginx:alpine
COPY static/ /usr/share/nginx/html/
RUN printf "add_header X-Content-Type-Options nosniff;\nadd_header X-Frame-Options DENY;\nadd_header X-XSS-Protection '1; mode=block';\n" > /etc/nginx/conf.d/security_headers.conf
