FROM mechtaev/ubuntu-16.04-llvm-3.8.1

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y && apt-get autoremove -y

RUN apt-get install -y build-essential \
                       curl \
                       wget \
                       libcap-dev \
                       git \
                       cmake \
                       libncurses5-dev \
                       nano \
                       psmisc  \
                       unzip \
                       libtcmalloc-minimal4 \
                       libgoogle-perftools-dev \
                       software-properties-common \
                       libssl-dev \
                       zlib1g-dev

# WORKDIR /home
# RUN mkdir clang-llvm
# WORKDIR /home/clang-llvm
# RUN git clone https://github.com/llvm/llvm-project.git && \
#     git clone https://github.com/martine/ninja.git && \
#     git clone https://github.com/Kitware/CMake.git
# WORKDIR /home/clang-llvm/ninja
# RUN git checkout release && ./bootstrap.py && \
#     cp ninja /usr/bin/

# WORKDIR /home/clang-llvm/CMake
# RUN git checkout release && ./bootstrap && make && make install

# WORKDIR /home/clang-llvm/llvm-project
# RUN mkdir build && cd build && \
#   cmake -G Ninja ../llvm -DLLVM_ENABLE_PROJECTS="clang;clang-tools-extra" -DLLVM_BUILD_TESTS=ON && \
#   ninja && ninja check && ninja clang-test && ninja install



ENV LLVM_VERSION=6.0

RUN apt-get install -y clang-${LLVM_VERSION} \
                       llvm-${LLVM_VERSION} \
                       llvm-${LLVM_VERSION}-dev \
                       llvm-${LLVM_VERSION}-tools

ENV Z3_VERSION=4.8.4

WORKDIR /z3

RUN wget -qO- https://github.com/Z3Prover/z3/archive/z3-${Z3_VERSION}.tar.gz | tar xz --strip-components=1 && \
    python scripts/mk_make.py && \
    cd build && \
    make && \
    make install

ENV PATH=/usr/lib/llvm-${LLVM_VERSION}/bin/:${PATH}

ENV KLEE_UCLIBC_VERSION=klee_0_9_29

WORKDIR /klee-uclibc

RUN git clone https://github.com/klee/klee-uclibc.git . && \
    git checkout ${KLEE_UCLIBC_VERSION} && \
    CC=clang ./configure --make-llvm-lib && \ 
    make -j2

ENV KLEE_VERSION=2.0

WORKDIR /klee 
RUN git clone https://github.com/rshariffdeen/klee.git source; cd source; git checkout concolic
RUN mkdir build && \
    cd build && \
    cmake \
        -DENABLE_SOLVER_Z3=ON \
        -DENABLE_POSIX_RUNTIME=ON \
        -DENABLE_KLEE_UCLIBC=ON \
        -DKLEE_UCLIBC_PATH=/klee-uclibc \
        -DENABLE_UNIT_TESTS=OFF \
        -DENABLE_SYSTEM_TESTS=OFF \
            ../source && \
    make

ENV PATH=/klee/build/bin/:${PATH}

ENV LLVM_COMPILER=clang

RUN add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y  --no-install-recommends --force-yes \
    bear \
    python3.7 \
    python3-pip

RUN python3.7 -m pip install --upgrade pip
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install setuptools
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install pylint
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install pysmt
RUN pysmt-install --z3 --confirm-agreement
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install funcy
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install six
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install numpy
RUN python3.7 -m pip --disable-pip-version-check --no-cache-dir install wllvm; return 0;

RUN git clone https://47493629a358a5b8c9d5387bb4271194c71b2921:x-oauth-basic@github.com/mechtaev/concolic-repair.git /CPR
WORKDIR /CPR
RUN cd lib && KLEE_INCLUDE_PATH=/klee/source/include make
ENV DEBIAN_FRONTEND=dialog
ENV TRIDENT_CC=/CPR/tools/trident-cc
ENV TRIDENT_CXX=/CPR/tools/trident-cxx

RUN cd /klee/build/lib; ar rcs libkleeRuntest.a libkleeRuntest.so.1.0

