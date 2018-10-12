FROM solr:6.5.0

COPY ./. /home/

EXPOSE 8983
WORKDIR /opt/solr

RUN mkdir -p /opt/solr/server/solr/mycores/proposal && \
  bin/solr start && \
  bin/solr create -c proposal && \
  bin/solr stop -all && \
  mkdir -p /opt/solr/server/solr/proposal/conf/mapping && \
  cp -f /home/instance/conf/mapping/*.txt /opt/solr/server/solr/proposal/conf/mapping/ && \
  cp -f /home/instance/conf/lang/*.txt /opt/solr/server/solr/proposal/conf/lang/ && \
  cp -f /home/instance/conf/*.txt /opt/solr/server/solr/proposal/conf/ && \
  cp -f /home/instance/conf/solrconfig.xml /opt/solr/server/solr/proposal/conf/solrconfig.xml && \
  cp -f /home/instance/core.properties /opt/solr/server/solr/proposal/core.properties && \
  cp -f /home/instance/schema.xml /opt/solr/server/solr/proposal/schema.xml
