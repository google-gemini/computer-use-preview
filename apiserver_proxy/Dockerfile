FROM nginx:latest

# Remove the default Nginx configuration file
RUN rm /etc/nginx/conf.d/default.conf

# Copy your custom Nginx configuration file into the container
# This file defines the reverse proxy rules
COPY nginx.conf /etc/nginx/conf.d/nginx.conf

# Expose port 80 for HTTP traffic (and 443 if using HTTPS)
EXPOSE 8080

COPY start.sh /usr/local/bin/start.sh

CMD ["/usr/local/bin/start.sh"]
