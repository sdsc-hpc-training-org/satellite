FROM debian:latest as os_with_packages
ENV PYTHONUNBUFFERED 1
RUN  \
  echo "Adding users" && \
  groupadd -g 56 ssl-cert && \
  \
  # for dehydrated/letsencrypt \
  groupadd -g 200 certs && \
  useradd -g certs -u 200 -M -s /bin/bash -d / certs && \
  \
  echo "Fetching package lists" && \
  apt-get update && \
  \
  echo "Upgrading base distribution to latest packages" && \
  apt-get dist-upgrade -y && \
  \
  echo "Adding packages" && \
  apt-get install -y \ 
    apache2 \
    git \
    curl \
    wget \
    vim \
    libcgi-pm-perl \
    libdbd-sqlite3-perl \
    sqlite3 \
    libnet-ip-perl \
    iptables \
    lsof \
    net-tools \
    apt-transport-https \
    software-properties-common \
    openssh-server && \
  \
  mkdir -p /var/www/satellite 


FROM os_with_packages AS all_configured
ENV PYTHONUNBUFFERED 1
RUN \
  umask 0022 && \
  a2enmod setenvif && \
  a2enmod socache_shmcb && \
  a2enmod remoteip && \
  a2dismod mpm_event && \
  a2enmod mpm_prefork && \
  a2enmod cgi && \
  a2enmod rewrite && \
  a2enmod proxy && \
  a2enmod proxy_http && \
  a2enmod proxy_html && \
  a2enmod proxy_wstunnel && \
  a2dismod ssl 
COPY image-files/ /


FROM all_configured AS satellite_added
ENV PYTHONUNBUFFERED 1
COPY bin cgi doc dynconf etc html httpd-conf logs var /var/www/satellite
CMD ["exec", "/entrypoint"]
