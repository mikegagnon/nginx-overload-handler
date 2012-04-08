
Install thrift dependencies (assuming Ubunutu)

    sudo apt-get install \
        libboost-dev \
        libboost-test-dev \
        libboost-program-options-dev \
        libevent-dev \
        automake \
        libtool \
        flex \
        bison \
        pkg-config \
        g++ \
        libssl-dev

./configure

make sure "Building Python Library ...... : yes" and not no

make
sudo make install


