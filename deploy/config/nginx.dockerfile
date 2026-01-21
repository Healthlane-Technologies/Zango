FROM nginx:latest

COPY config/nginx.conf /etc/nginx/conf.d/default.conf
CMD [ "nginx", "-g", "daemon off;" ]
