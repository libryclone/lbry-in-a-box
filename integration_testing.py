"""

Integration testing using lbry-in-a-box

"""

import unittest
import subprocess
import time

from bitcoinrpc.authproxy import AuthServiceProxy
from jsonrpc.proxy import JSONRPCProxy

lbrycrd_rpc_user='rpcuser'
lbrycrd_rpc_pw='jhopfpusrx'
lbrycrd_rpc_ip='127.0.0.1'
lbrycrd_rpc_port='19001'
lbrynet_rpc_port = '5279'
dht_rpc_port = '5278'
reflector_rpc_port = '5277'

lbrynet = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(lbrynet_rpc_port))
dht = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(dht_rpc_port))
reflector = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(reflector_rpc_port))


def shell_command(command):
    p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE)
    out,err = p.communicate()
    return out,err


def call_lbrycrd(method,*params):
    lbrycrd = AuthServiceProxy("http://{}:{}@{}:{}".format(lbrycrd_rpc_user,lbrycrd_rpc_pw,
                                                            lbrycrd_rpc_ip,lbrycrd_rpc_port))
    return getattr(lbrycrd,method)(*params)


class LbrynetTest(unittest.TestCase):

    def test_lbrynet(self):
        self._test_lbrynet_startup()
        self._test_recv()
        self._test_send()
        self._test_publish()

    def _increment_blocks(self, num_blocks):
        LBRYNET_BLOCK_SYNC_TIMEOUT = 60

        out = call_lbrycrd('generate',num_blocks)
        self.assertEqual(len(out),num_blocks)
        for blockhash in out:
            self._is_blockhash(blockhash)

        # wait till all lbrynet instances in sync with the
        # tip of the blockchain
        best_block_hash = call_lbrycrd('getbestblockhash')
        self._is_blockhash(best_block_hash)
        start_time = time.time()
        while time.time() - start_time < LBRYNET_BLOCK_SYNC_TIMEOUT:
            lbrynet_synced = lbrynet.get_best_blockhash() == best_block_hash
            dht_synced = dht.get_best_blockhash() == best_block_hash
            reflector_synced = reflector.get_best_blockhash() == best_block_hash
            if lbrynet_synced and dht_synced and reflector_synced:
                return
            time.sleep(0.01)
        self.fail('Lbrynet block sync timed out')

    def _is_txid(self, txid):
        self.assertEqual(len(txid),64)

    def _is_blockhash(self, blockhash):
        self.assertEqual(len(blockhash),64)

    def _wait_for_lbrynet_sync(self):
        time.sleep(60)

    # wait and test to see if lbrynet startups
    def _test_lbrynet_startup(self):
        LBRYNET_STARTUP_TIMEOUT = 60
        start_time = time.time()
        while time.time() - start_time < LBRYNET_STARTUP_TIMEOUT:
            if lbrynet.is_running():
                print("Lbrynet startup detected")
                self.assertEqual(0, lbrynet.get_balance())
                self.assertEqual(True, lbrynet.is_first_run())
                return
            time.sleep(0.01)

        self.fail('Lbrynet failed to start up')

    # receive balance from lbrycrd to lbrynet
    def _test_recv(self):
        RECV_AMOUNT = 10
        address = lbrynet.get_new_address()
        out = call_lbrycrd('sendtoaddress',address,RECV_AMOUNT)
        self._is_txid(out)
        self._increment_blocks(6)
        self._wait_for_lbrynet_sync()
        balance = lbrynet.get_balance()
        self.assertEqual(RECV_AMOUNT, balance)

    #send balance from lbrynet back to lbrycrd
    def _test_send(self):
        SEND_AMOUNT = 1
        # create lbrycrd address
        address = call_lbrycrd('getnewaddress','test')
        out = call_lbrycrd('getbalance','test')
        self.assertEqual(0,out)

        # send from lbrynet to lbrycrd
        out = lbrynet.send_amount_to_address({'amount':SEND_AMOUNT, 'address':address})
        self.assertEqual(out,True)
        self._wait_for_lbrynet_sync()
        self._increment_blocks(6)
        out = call_lbrycrd('getbalance', 'test')
        self.assertEqual(SEND_AMOUNT, out)

    # test publishing from lbrynet, and test to see if we can download from dht 
    def _test_publish(self):
        CLAIM_AMOUNT = 1
        # make sure we have enough amount
        out = lbrynet.get_balance()
        self.assertTrue(out >= CLAIM_AMOUNT)

        test_metadata = {
            'license': 'NASA',
            'ver': '0.0.3',
            'description': 'test',
            'language': 'en',
            'author': 'test',
            'title': 'test',
            'nsfw': False,
            'content_type': 'video/mp4',
            'thumbnail': 'test'
        }
        out = lbrynet.publish({'name':'testname','file_path':'/src/lbry/FAQ.md','bid':CLAIM_AMOUNT,'metadata':test_metadata})
        publish_txid = out['txid']
        publish_nout = out['nout']
        self._is_txid(publish_txid)
        self.assertTrue(isinstance(publish_nout,int))

        self._wait_for_lbrynet_sync()
        self._increment_blocks(6)

        # check lbrycrd claim state is updated
        out = call_lbrycrd('getvalueforname','testname')
        self.assertEqual(out['amount'],CLAIM_AMOUNT*100000000)
        self.assertEqual(out['effective amount'],CLAIM_AMOUNT*100000000)
        self.assertEqual(out['txid'],publish_txid)
        self.assertEqual(out['n'],publish_nout)

        # check lbrynet claim state is updated
        out = lbrynet.get_claim_info({'name':'testname'})
        self.assertEqual('testname', out['name'])
        self.assertEqual(publish_txid, out['txid'])
        self.assertEqual(publish_nout, out['nout'])
        self.assertEqual(CLAIM_AMOUNT, out['amount'])
        self.assertEqual([],out['supports'])

        sd_hash = out['value']['sources']['lbry_sd_hash']

        # test download of own file
        out = lbrynet.get({'name':'testname'})
        self.assertEqual('/data/Downloads/FAQ.md',out['path'])
        self.assertEqual(sd_hash, out['stream_hash'])

        # check to see if we can access sd_hash
        out = lbrynet.download_descriptor({'sd_hash':sd_hash})
        blob_hash = out['blobs'][0]['blob_hash']

        # check that we have all the hashes
        out = lbrynet.get_blob_hashes()
        self.assertTrue(sd_hash in out)
        self.assertTrue(blob_hash in out)

        # check reflector to see if it can access sd_hash
        out = reflector.download_descriptor({'sd_hash':sd_hash})
        self.assertEqual(blob_hash,out['blobs'][0]['blob_hash'])

        # check reflector to see if it has hashes
        out = reflector.get_blob_hashes()
        self.assertTrue(sd_hash in out)
        self.assertTrue(blob_hash in out)

        # test to see if we can get peers from the dht with the hash
        out = dht.get_peers_for_hash({'blob_hash':sd_hash})
        self.assertEqual(2, len(out))

        # test to see if we can download from dht
        out = dht.get({'name':'testname'})
        self.assertEqual('/data/Downloads/FAQ.md',out['path'])
        self.assertEqual(sd_hash, out['stream_hash'])

        # check to see if dht has the downloaded hashes
        out = dht.get_blob_hashes()
        self.assertTrue(sd_hash in out)
        self.assertTrue(blob_hash in out)

        # TODO: we should log into the dht docker instance and check for file presense and diff it against original

if __name__ == '__main__':
    # Make sure to rebuild docker instances
    out,err=shell_command('docker-compose down')
    out,err=shell_command('docker-compose rm -f')
    out,err=shell_command('docker-compose build')

    out,err=shell_command('docker-compose up > tmp.log&')
    # Wait for docker containter start up
    # TODO: we should retry connections until they can be reached here
    # instead of sleeping
    time.sleep(60)
    unittest.main()

