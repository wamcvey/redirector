FROM traefik:v2.3

COPY traefik-config.d /traefik-config.d
CMD ["--entryPoints.web.address=:80", "--log.level=INFO", "--providers.file.directory=/traefik-config.d" ]




