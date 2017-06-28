# Docker file for JuliaBox APIs
# Version:42

FROM ubuntu:16.04

MAINTAINER Tanmay Mohapatra

RUN apt-get update \
    && apt-get upgrade -y -o Dpkg::Options::="--force-confdef" -o DPkg::Options::="--force-confold" \
    && apt-get install -y \
    man-db \
    libc6 \
    libc6-dev \
    build-essential \
    wget \
    curl \
    file \
    vim \
    screen \
    tmux \
    unzip \
    pkg-config \
    cmake \
    gfortran \
    gettext \
    libreadline-dev \
    libncurses-dev \
    libpcre3-dev \
    libgnutls28-dev \
    libzmq3-dev \
    python \
    python-yaml \
    python-m2crypto \
    python-crypto \
    msgpack-python \
    python-dev \
    python-setuptools \
    supervisor \
    python-jinja2 \
    python-requests \
    python-isodate \
    python-git \
    python-pip \
    && apt-get clean

RUN pip install --upgrade pyzmq PyDrive google-api-python-client==1.5.2 jsonpointer jsonschema tornado sphinx pygments nose readline mistune invoke

RUN pip install --upgrade 'ipython<6.0' 'notebook<6.0'

RUN pip install 'rise<6.0'; jupyter-nbextension install rise --py --sys-prefix; jupyter-nbextension enable rise --py --sys-prefix

RUN ln -fs /opt/julia/bin/julia /usr/bin/julia

# add juser
# create group and user with specific ids if required on systems where the user running juliabox is not the first user
RUN groupadd juser \
    && useradd -m -d /home/juser -s /bin/bash -g juser -G staff juser \
    && echo "export HOME=/home/juser" >> /home/juser/.bashrc

# add Julia v0.5
RUN mkdir -p /opt/julia-0.5.2 && \
    curl -s -L https://julialang-s3.julialang.org/bin/linux/x64/0.5/julia-0.5.2-linux-x86_64.tar.gz | tar -C /opt/julia-0.5.2 -x -z --strip-components=1 -f -
RUN ln -fs /opt/julia-0.5.2 /opt/julia-0.5

# add Julia v0.6
RUN mkdir -p /opt/julia-0.6.0 && \
    curl -s -L https://julialang-s3.julialang.org/bin/linux/x64/0.6/julia-0.6.0-linux-x86_64.tar.gz | tar -C /opt/julia-0.6.0 -x -z --strip-components=1 -f -
RUN ln -fs /opt/julia-0.6.0 /opt/julia-0.6

# Make Julia 0.6 the default
RUN rm -f /opt/julia && ln -fs /opt/julia-0.6 /opt/julia

USER juser
ENV HOME /home/juser
ENV PATH /usr/local/texlive/2014/bin/x86_64-linux:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin:/opt/julia/bin
WORKDIR /home/juser

RUN /opt/julia-0.5/bin/julia -e "(Pkg.installed(\"JuliaWebAPI\") == nothing) && Pkg.add(\"JuliaWebAPI\")"
RUN /opt/julia-0.6/bin/julia -e "(Pkg.installed(\"JuliaWebAPI\") == nothing) && Pkg.add(\"JuliaWebAPI\")"

ENTRYPOINT ["julia", "-e", "using JuliaWebAPI; using Compat; process();"]
