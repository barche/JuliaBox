#!/bin/bash

function init_packages {
    JULIA_VER=$1
    /opt/julia-${JULIA_VER}/bin/julia -e "Pkg.init()"
}

function include_packages {
    JULIA_VER=$1
    PKG_LIST=$2
    METHOD=$3
    for PKG in $PKG_LIST
    do
        echo ""
        echo "$METHOD package $PKG to Julia $JULIA_VER ..."
        /opt/julia-${JULIA_VER}/bin/julia -e "Pkg.${METHOD}(\"$PKG\")"
    done
}

function precompile_packages {
    JULIA_VER=$1
    PKG_LIST=$2
    for PKG in $PKG_LIST
    do
        echo ""
        echo "Precompiling package $PKG to Julia $JULIA_VER ..."
        /opt/julia-${JULIA_VER}/bin/julia -e "using $PKG"
    done
}

function list_packages {
    JULIA_VER=$1
    echo ""
    echo "Listing packages for Julia $JULIA_VER ..."
    /opt/julia-${JULIA_VER}/bin/julia -e 'println("JULIA_HOME: $JULIA_HOME\n"); versioninfo(); println(""); Pkg.status()' > /opt/julia_packages/julia-${JULIA_VER}.packages.txt
}

# Install packages for Julia 0.5 and 0.6
DEFAULT_PACKAGES="IJulia PyPlot Interact Colors SymPy PyCall Plots TikzPictures GR SimJulia Unitful PlotlyJS PGFPlots StaticArrays BenchmarkTools"
INTERNAL_PACKAGES="https://github.com/tanmaykm/JuliaBoxUtils.jl.git"
BUILD_PACKAGES="JuliaBoxUtils IJulia PyPlot"
CHECKOUT_PACKAGES="GR"

for ver in 0.5 0.6
do
    init_packages "$ver"
    include_packages "$ver" "$DEFAULT_PACKAGES" "add"
    include_packages "$ver" "$INTERNAL_PACKAGES" "clone"
    include_packages "$ver" "$BUILD_PACKAGES" "build"
    include_packages "$ver" "$CHECKOUT_PACKAGES" "add"
    include_packages "$ver" "$CHECKOUT_PACKAGES" "checkout"
    include_packages "$ver" "$CHECKOUT_PACKAGES" "build"
    precompile_packages "$ver" "$DEFAULT_PACKAGES"
    precompile_packages "$ver" "$BUILD_PACKAGES"
    precompile_packages "$ver" "$CHECKOUT_PACKAGES"
    list_packages "$ver"
done
