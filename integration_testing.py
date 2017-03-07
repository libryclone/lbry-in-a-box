"""
Integration testing using lbry-in-a-box

This will stop,rebuild and launch docker containers for lbry in a box,
and than run integration testing

"""

import unittest
import subprocess
import time
from jsonrpc.proxy import JSONRPCProxy
from bitcoinrpc.authproxy import AuthServiceProxy

from urllib2 import URLError
from httplib import BadStatusLine
from socket import error
import os

lbrycrd_rpc_user='rpcuser'
lbrycrd_rpc_pw='jhopfpusrx'
lbrycrd_rpc_ip='127.0.0.1'
lbrycrd_rpc_port='19001'
lbrynet_rpc_port = '5279'
dht_rpc_port = '5278'
reflector_rpc_port = '5277'

lbrynets={}
lbrynets['lbrynet'] = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(lbrynet_rpc_port))
lbrynets['dht'] = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(dht_rpc_port))
lbrynets['reflector'] = JSONRPCProxy.from_url("http://localhost:{}/lbryapi".format(reflector_rpc_port))

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

DOCKER_LOG_FILE='tmp.log'
NUM_INITIAL_BLOCKS_GENERATED = 150

def shell_command(command):
    p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE)
    out,err = p.communicate()
    return out,err


def call_lbrycrd(method, *params):
    lbrycrd = AuthServiceProxy("http://{}:{}@{}:{}".format(lbrycrd_rpc_user,lbrycrd_rpc_pw,
                                                            lbrycrd_rpc_ip,lbrycrd_rpc_port))
    return getattr(lbrycrd,method)(*params)

# wrapper function just to see where we are in the test
def print_func(func):
    def wrapper(*args,**kwargs):
        print("Running:{}".format(func.func_name))
        return func(*args,**kwargs)
    return wrapper

class LbrynetTest(unittest.TestCase):

    def test_lbrynet(self):
        self._test_lbrynet_startup()
        self._test_recv_and_send()
        # test publish and download of free content
        self._test_publish('testname',1,)
        # test publish and download of non free content
        self._test_publish('testname2',1,1)
        self._test_update()

        # TODO: should try to remove all errors here, raise error if found
        print("Printing ERRORS found in log:")
        out,err = shell_command('grep ERROR {}'.format(DOCKER_LOG_FILE))
        print out

    # generate random test file at lbrynet instance
    def _generate_test_file(self, file_size_bytes, file_path):

        cmd = 'docker exec -it lbryinabox_lbrynet_1 dd if=/dev/urandom of={} bs={} count=1'.format(file_path, file_size_bytes)
        #cmd = 'docker exec -it lbryinabox_lbrynet_1 head -c {} </dev/urandom >{}'.format(file_size_bytes, file_path)
        out,err = shell_command(cmd)


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
            if all([lbrynet.get_best_blockhash() == best_block_hash for lbrynet in lbrynets.values()]):
                return
            time.sleep(0.1)
        self.fail('Lbrynet block sync timed out')

    def _is_txid(self, txid):
        self.assertEqual(len(txid),64)

    def _is_blockhash(self, blockhash):
        self.assertEqual(len(blockhash),64)

    def _wait_till_balance_equals(self,lbrynet,amount):
        LBRYNET_SYNC_TIMEOUT = 30
        start_time = time.time()
        while time.time() - start_time < LBRYNET_SYNC_TIMEOUT:
            if lbrynet.get_balance() == amount:
                return
            time.sleep(0.01)
        self.fail('Lbrynet failed to sync balance in time')

    def _wait_for_lbrynet_sync(self):
        time.sleep(40)

    # send amount from lbrycrd to lbrynet instance
    def _send_from_lbrycrd(self, amount, to_lbrynet):
        LBRYNET_RECV_TIMEOUT = 60
        prev_balance = to_lbrynet.get_balance()
        address = to_lbrynet.get_new_address()
        out = call_lbrycrd('sendtoaddress',address,amount)
        self._is_txid(out)
        self._increment_blocks(6)
        self._wait_till_balance_equals(to_lbrynet,prev_balance+amount)


    def _check_lbrynet_init(self,lbrynet):
        try:
            lbrynet_status = lbrynet.status()
        except (URLError,error,BadStatusLine) as e:
            return False

        if lbrynet_status['is_running'] == True:
            self.assertEqual(0, lbrynet.get_balance())
            self.assertEqual(True, lbrynet_status['is_first_run'])
            self.assertEqual(0, lbrynet_status['blocks_behind'])
            self.assertEqual(NUM_INITIAL_BLOCKS_GENERATED, lbrynet_status['blockchain_status']['blocks'])
            return True
        else:
            return False

    @print_func
    def _test_lbrynet_startup(self):
        LBRYNET_STARTUP_TIMEOUT = 120

        # Make sure to rebuild docker instances
        out,err=shell_command('docker-compose down')
        out,err=shell_command('docker-compose rm -f')
        out,err=shell_command('docker-compose build')
        out,err=shell_command('docker-compose up > {}&'.format(DOCKER_LOG_FILE))

        start_time = time.time()
        while time.time() - start_time < LBRYNET_STARTUP_TIMEOUT:
            if all([self._check_lbrynet_init(lbrynet) for lbrynet in lbrynets.values()]):
                return
            time.sleep(3)
        self.fail('Lbrynet failed to start up')

    # receive balance from lbrycrd to lbrynet
    @print_func
    def _test_recv_and_send(self):
        RECV_AMOUNT = 10
        SEND_AMOUNT = 1
        LBRYNET_SEND_SYNC_TIMEOUT = 60
        self._send_from_lbrycrd(RECV_AMOUNT,lbrynets['lbrynet'])

        # create lbrycrd address
        address = call_lbrycrd('getnewaddress','test')
        out = call_lbrycrd('getbalance','test')
        self.assertEqual(0,out)

        # send from lbrynet to lbrycrd
        out = lbrynets['lbrynet'].send_amount_to_address({'amount':SEND_AMOUNT, 'address':address})
        self.assertEqual(out,True)

        # wait for lbrycrd to sync balance
        start_time = time.time()
        while call_lbrycrd('getreceivedbyaccount','test',0) < SEND_AMOUNT:
            if time.time() - start_time > LBRYNET_SEND_SYNC_TIMEOUT:
                self.fail('Lbrynet send failed to sync within time')
            time.sleep(0.01)
        self._increment_blocks(6)
        out = call_lbrycrd('getbalance', 'test')
        self.assertEqual(SEND_AMOUNT, out)

    def _publish(self, claim_name, claim_amount, key_fee, test_pub_file, test_pub_file_size):
        # make sure we have enough to claim the amount
        out = lbrynets['lbrynet'].get_balance()
        self.assertTrue(out >= claim_amount)

        if key_fee != 0:
            key_fee_address = lbrynets['lbrynet'].get_new_address()
            test_metadata["fee"]= {'LBC': {"address": key_fee_address, "amount": key_fee}}

        self._generate_test_file(test_pub_file_size, test_pub_file)

        out = lbrynets['lbrynet'].publish({'name':claim_name,'file_path':test_pub_file,'bid':claim_amount,'metadata':test_metadata})
        publish_txid = out['txid']
        publish_nout = out['nout']
        self._is_txid(publish_txid)
        self.assertTrue(isinstance(publish_nout,int))

        self._wait_for_lbrynet_sync()
        self._increment_blocks(6)
        return publish_txid,publish_nout



    # test publishing from lbrynet, and test to see if we can download from dht
    @print_func
    def _test_publish(self, claim_name, claim_amount, key_fee = 0):
        test_pub_file_name = claim_name+'.txt'
        test_pub_file_dir = '/src/lbry'
        test_pub_file = os.path.join(test_pub_file_dir,test_pub_file_name)
        expected_download_file = os.path.join('/data/Downloads/',test_pub_file_name)
        publish_txid, publish_nout = self._publish(claim_name, claim_amount, key_fee, test_pub_file, 1024)

        balance_before_key_fee = lbrynets['lbrynet'].get_balance()

        # check lbrycrd claim state is updated
        out = call_lbrycrd('getvalueforname',claim_name)
        self.assertEqual(out['amount'],claim_amount*100000000)
        self.assertEqual(out['effective amount'],claim_amount*100000000)
        self.assertEqual(out['txid'],publish_txid)
        self.assertEqual(out['n'],publish_nout)

        # check lbrynet claim state is updated
        out = lbrynets['lbrynet'].claim_show({'name':claim_name})
        self.assertEqual(claim_name, out['name'])
        self.assertEqual(publish_txid, out['txid'])
        self.assertEqual(publish_nout, out['nout'])
        self.assertEqual(claim_amount, out['amount'])
        self.assertEqual([],out['supports'])

        sd_hash = out['value']['sources']['lbry_sd_hash']

        out = lbrynets['lbrynet'].claim_list_mine({'name':claim_name})
        self.assertTrue(isinstance(out,dict))
        self.assertEqual(claim_name,out['name'])
        self.assertEqual(claim_amount,out['amount'])


        # test download of own file
        out = lbrynets['lbrynet'].get({'name':claim_name})
        self.assertEqual(expected_download_file,out['path'])
        self.assertEqual(sd_hash, out['stream_hash'])

        # check file is under file list
        out = lbrynets['lbrynet'].file_list()
        found_file = False
        for f in out:
            if( f['sd_hash'] == sd_hash and f['lbry_uri'] == claim_name and
                f['download_path'] == expected_download_file ):
                found_file = True
        self.assertTrue(found_file)

        # check file is under file_get
        out = lbrynets['lbrynet'].file_get({'name':claim_name})
        self.assertEqual(out['sd_hash'], sd_hash)
        self.assertEqual(out['lbry_uri'], claim_name)
        self.assertEqual(out['download_path'], expected_download_file)

        # check that we can get its blob
        out = lbrynets['lbrynet'].blob_list({'sd_hash':sd_hash})
        self.assertEqual(1, len(out))
        blob_hash = out[0]

        # check reflector to see if it has hashes
        out = lbrynets['reflector'].get_blob_hashes()
        self.assertTrue(sd_hash in out)
        self.assertTrue(blob_hash in out)

        # test to see if we can get peers from the dht with the hash
        out = lbrynets['dht'].get_peers_for_hash({'blob_hash':sd_hash})
        self.assertEqual(2, len(out))

        # test to see if we can download from dht
        if key_fee != 0:
            # send key fee (plus additional amount to pay for tx fee) to dht if necessary
            self._send_from_lbrycrd(key_fee+1, lbrynets['dht'])

        out = lbrynets['dht'].get({'name':claim_name})
        self.assertEqual(expected_download_file, out['path'])
        self.assertEqual(sd_hash, out['stream_hash'])

        # check to see if dht has the downloaded hashes
        out = lbrynets['dht'].get_blob_hashes()
        self.assertTrue(sd_hash in out)
        self.assertTrue(blob_hash in out)

        # check if dht has the file
        cmd = 'docker exec -it lbryinabox_dht_1 find {}'.format(expected_download_file)
        out,err = shell_command(cmd)
        self.assertFalse('No such file' in out)
        self.assertTrue(expected_download_file in out)

        # test to see if lbrynet received key fee
        if key_fee != 0:
            self._wait_for_lbrynet_sync()
            self._increment_blocks(6)
            self._wait_till_balance_equals(lbrynets['lbrynet'], balance_before_key_fee+key_fee)


    def _test_update(self, claim_name='updatetest', claim_amount=1, key_fee=0 ):
        test_pub_file_name = claim_name+'.txt'
        test_pub_file_dir = '/src/lbry'
        test_pub_file = os.path.join(test_pub_file_dir,test_pub_file_name)
        expected_download_file = os.path.join('/data/Downloads/',test_pub_file_name)
        publish_txid, publish_nout = self._publish(claim_name, claim_amount, key_fee, test_pub_file, 1024)

        #  download from dht
        out = lbrynets['dht'].get({'name':claim_name})

        test_pub_file_name = claim_name+'2.txt'
        test_pub_file_dir = '/src/lbry'
        test_pub_file = os.path.join(test_pub_file_dir,test_pub_file_name)
        expected_download_file = os.path.join('/data/Downloads/',test_pub_file_name)
        update_publish_txid, update_publish_nout = self._publish(claim_name, claim_amount, key_fee, test_pub_file, 1024)

        # check claimtrie state is updated
        out = lbrynets['lbrynet'].claim_show({'name':claim_name})
        self.assertEqual(claim_name, out['name'])
        self.assertEqual(update_publish_txid, out['txid'])
        self.assertEqual(update_publish_nout, out['nout'])


if __name__ == '__main__':

    unittest.main()


