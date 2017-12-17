import base64
import click
import hashlib
import os
import select
import sys
import tempfile
from Crypto import Random 
from Crypto.Cipher import AES
from getpass import getpass
from subprocess import call

UNLOCKED_KEY='/tmp/1jmoz'

class AESCipher(object):

    def __init__(self, key): 
        self.bs = 32
        self.key = key

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s)-1:])]

def get_crypto():
    if os.path.isfile(UNLOCKED_KEY):
        with open(UNLOCKED_KEY, 'r') as f:
            key = f.read()
    else:
        print """Key is not open, you will need to unlock it."""
        password = getpass()
        with open(UNLOCKED_KEY, 'w+') as f:
            duration = input('How long should this session remain open (minutes): ')
            duration = duration * 60

            # How long should we keep this session open?
            call('sleep %s && rm %s &' % (duration, UNLOCKED_KEY), shell=True)

            key = hashlib.sha256(password.encode()).digest()
            f.write(key)

    
    return AESCipher(key)


@click.group()
def cli():
    """ manages passwords """

@cli.command('new')
@click.argument('f', nargs=1)
def new(f):
    crypto = get_crypto()
    if not sys.stdin.isatty():
        raw = sys.stdin
    else:
        call(['vim', f])
        tf = open(f, 'r')
        raw = tf.read()
        os.remove(f)

    with open('%s.enc' % f, 'wt') as fin:
        fin.write(crypto.encrypt(raw))

@cli.command('show')
@click.argument('f', nargs=1)
def show(f):
    crypto = get_crypto()

    with open('%s' % f, 'r') as f:
        enc = f.read()
        print crypto.decrypt(enc)

if __name__ == '__main__':
    cli()
