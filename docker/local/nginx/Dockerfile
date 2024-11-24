# Define the base image
FROM nginx:1.27.2-alpine

# Remove the default nginx.conf file that comes with the official nginx image
# and replace it with our own custom default.conf file.
# This is necessary because the default.conf file is not configurable and
# does not allow us to set up the reverse proxy as we need it.
RUN rm /etc/nginx/conf.d/default.conf

# Copy our custom nginx.conf from the current directory into the container
# at the path /etc/nginx/conf.d/default.conf.
# This file will be used to configure the reverse proxy.
COPY ./default.conf /etc/nginx/conf.d/default.conf