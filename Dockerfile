FROM maven:3-jdk-8

RUN apt-get update

RUN apt-get install -y python3 python3-pip git && \
pip install pandas && \
pip install jupyterlab_server && \
pip install networkx && \
pip install colourmap && \
pip install python-louvain && \
pip install community && \
pip install sklearn && \
pip install ismember && \
pip install PyGithub && \
pip install -U jinja2==2.11.3

COPY . /


ENV M2_HOME=/usr/share/maven

# set up Maven local repo
RUN mkdir /root/.m2 && mkdir /root/.m2/repository && echo \
    "<settings xmlns='http://maven.apache.org/SETTINGS/1.0.0\' \
    xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' \
    xsi:schemaLocation='http://maven.apache.org/SETTINGS/1.0.0 https://maven.apache.org/xsd/settings-1.0.0.xsd'> \
        <localRepository>/root/.m2/repository</localRepository> \
        <interactiveMode>true</interactiveMode> \
        <usePluginRegistry>false</usePluginRegistry> \
        <offline>false</offline> \
    </settings>" \
    > /root/.m2/settings.xml 

CMD python3 api-viz.py