FROM httpd:2.4

ENV REPO_PASSWORD=""

COPY ./configs/httpd_auth.conf /usr/local/apache2/conf/httpd_auth.conf
RUN ["mkdir", "passwd"]
COPY ./scripts/start.sh .
EXPOSE 80 443

CMD ["./start.sh"]