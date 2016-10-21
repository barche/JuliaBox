# Docker file for JuliaBox
# Version:42

FROM ubuntu:14.04
# Switching the base to the bare julia image helps during JuliaBox development by reducing image size
# FROM julialang/julia:v0.3.12

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
    libgnutls28 \
    libxext6 \
    libxtst6 \
    libzmq3-dev \
    libzmq3 \
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

RUN apt-get update && apt-get install -y texlive-latex-base texlive-latex-extra texlive-latex-recommended

RUN apt-get update \
    && apt-get install -y \
    imagemagick \
    inkscape \
    pandoc \
    pdf2svg \
    hdf5-tools \
    python-sympy \
    python-numpy \
    python-scipy \
    python-matplotlib \
    glpk-utils \
    && apt-get clean

# Cairo
RUN apt-get install -y \
    gettext \
    libpango1.0-dev \
    libpango1.0-0 \
    libgvc6 \
    graphviz \
    libgraphviz-dev \
    && apt-get clean

# SymPy
RUN pip install --upgrade sympy

RUN pip install --upgrade pyzmq PyDrive google-api-python-client jsonpointer jsonschema tornado sphinx pygments nose readline mistune invoke

RUN pip install 'notebook==4.2'

RUN pip install 'rise==4.0.0b1'; jupyter-nbextension install rise --py --sys-prefix; jupyter-nbextension enable rise --py --sys-prefix

RUN easy_install widgetsnbextension
RUN easy_install ipywidgets

RUN ln -fs /opt/julia/bin/julia /usr/bin/julia
RUN git clone https://github.com/tanmaykm/shellinabox_fork.git; cd shellinabox_fork; ./configure; make install; cd ..; rm -rf shellinabox_fork

# CloudArray dependencies
RUN apt-get install -y sshpass

# add juser
# create group and user with specific ids if required on systems where the user running juliabox is not the first user
RUN groupadd juser \
    && useradd -m -d /home/juser -s /bin/bash -g juser -G staff juser \
    && echo "export HOME=/home/juser" >> /home/juser/.bashrc

# add Julia v0.4 build
RUN mkdir -p /opt/julia-0.4.7 && \
    curl -s -L https://julialang.s3.amazonaws.com/bin/linux/x64/0.4/julia-0.4.7-linux-x86_64.tar.gz | tar -C /opt/julia-0.4.7 -x -z --strip-components=1 -f -
RUN ln -fs /opt/julia-0.4.7 /opt/julia-0.4

# add Julia v0.5
RUN mkdir -p /opt/julia-0.5.0 && \
    curl -s -L https://julialang.s3.amazonaws.com/bin/linux/x64/0.5/julia-0.5.0-linux-x86_64.tar.gz | tar -C /opt/julia-0.5.0 -x -z --strip-components=1 -f -
RUN ln -fs /opt/julia-0.5.0 /opt/julia-0.5

# Make Julia 0.5 the default
RUN rm -f /opt/julia && ln -fs /opt/julia-0.5 /opt/julia

# JuliaBox package bundle shall be mounted at /opt/julia_packages.
# They are added to LOAD_PATH through respective juliarc.jl scripts.
RUN mkdir /opt/julia_packages
RUN echo 'push!(LOAD_PATH, "/opt/julia_packages/.julia/v0.5/"); push!(Base.LOAD_CACHE_PATH, "/opt/julia_packages/.julia/lib/v0.5"); try using JuliaBoxUtils; JuliaBoxUtils.SysLim.setrlimit(JuliaBoxUtils.SysLim.RLIMIT_NOFILE, 256) end' >> /opt/julia-0.5/etc/julia/juliarc.jl
RUN echo 'push!(LOAD_PATH, "/opt/julia_packages/.julia/v0.4/"); push!(Base.LOAD_CACHE_PATH, "/opt/julia_packages/.julia/lib/v0.4"); try using JuliaBoxUtils; JuliaBoxUtils.SysLim.setrlimit(JuliaBoxUtils.SysLim.RLIMIT_NOFILE, 256) end' >> /opt/julia-0.4/etc/julia/juliarc.jl

# Data volumes shall be mounted at /mnt/data
RUN mkdir /mnt/data
RUN mkdir /opt/juliabox

RUN echo "ulimit -u 2048 -n 256" >> /etc/bash.bashrc

USER juser
ENV HOME /home/juser
ENV PATH /usr/local/texlive/2014/bin/x86_64-linux:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin:/opt/julia/bin
WORKDIR /home/juser

# 4200: http port for console
# 8000: http port for tornado
# 8998: ipython port for julia
# 8050-8052: user specified applications
EXPOSE  4200 8000 8998 8050 8051 8052

ENTRYPOINT ["/usr/bin/supervisord", "-n", "-c", "/opt/juliabox/.juliabox/supervisord.conf", "-l", "/opt/juliabox/.juliabox/supervisord.log", "-j", "/opt/juliabox/.juliabox/supervisord.pid", "-q", "/opt/juliabox/.juliabox"]
