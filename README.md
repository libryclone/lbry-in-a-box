# LBRY in a Box

Run all of the LBRY network locally inside docker containers. The LBRY
blockchain is configured to use `regtest`. This is intended as a tool
for developers to provide an isolated environment for testing.  Using
`regtest` has the advantage that coins are free and any bugs in
publishing or metadata won't propogate out to rest of the
network. Additionally, extra blocks can be mined on demand so there is
no need to wait for claims or transactions to propogate.

## Prerequesites 

- Install [docker](https://docs.docker.com/engine/installation/)
- Install [docker-compose](https://github.com/docker/compose/releases)

## Usage

    git clone --recursive git@github.com:lbryio/lbry-in-a-box.git
    cd lbry-in-a-box
    docker-compose up

To initialize the blockchain run:

 ```
 ./lbrycrd-cli -rpcconnect=127.0.0.1 -rpcport=19001 -rpcuser=rpcuser \
    -rpcpassword=jhopfpusrx -regtest=1 generate 150
 ```

The lbrynet daemon can now connect to your local lbryum server.  It
needs to be properly configured, which requires some code changes to allow
for that to happen (lbryum has been difficult to work with). This section
should be updated after those code changes happen.


## Container Configuration

Docker is very flexible in its ability to mount files and directories.
For each service, the behavior can be changed by mounting a
configuration file, or over-writing a data directory. At some point,
we'll probably have standard blockchain data and blob data that can be
pre-populated into the containers.

Check the Dockerfile and README files for each container for more information.


