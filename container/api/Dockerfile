# Docker file for JuliaBox APIs
# Version:42

FROM julialang/julia

MAINTAINER Tanmay Mohapatra

RUN ln -fs /opt/julia/bin/julia /usr/bin/julia

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
RUN rm /opt/julia && ln -fs /opt/julia-0.5 /opt/julia

USER juser
ENV HOME /home/juser
ENV PATH /usr/local/texlive/2014/bin/x86_64-linux:/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin:/opt/julia/bin
WORKDIR /home/juser

RUN /opt/julia-0.4/bin/julia -e "(Pkg.installed(\"JuliaWebAPI\") == nothing) && Pkg.add(\"JuliaWebAPI\")"
RUN /opt/julia-0.5/bin/julia -e "(Pkg.installed(\"JuliaWebAPI\") == nothing) && Pkg.add(\"JuliaWebAPI\")"

ENTRYPOINT ["julia", "-e", "using JuliaWebAPI; using Compat; process();"]
