
import re
import random
import hmac
import hashlib
import urllib2

from google.appengine.ext import db

from string import letters




"""Here are main functions for the Wikistems """

#form validation

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)


#user security 
secret = '{uD.O:M,[/hDJkIA:Bf5H=L$Ng;vVU'

def make_secure_val(val):
    return '%s|%s' %(val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split("|")[0]
    if secure_val == make_secure_val(val):
        return val

def make_salt(length=5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' %(salt,h)

def valid_pw(name, password, h):
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
    return db.Key.from_path('users', group)

def wiki_key(group = 'default'):
    return db.Key.from_path('wiki', group)

def get_referrer_html(referer):
    try:
        f = urllib2.urlopen(referer)
        return f.read()
    except:
        pass

def gray_style(lst):
    for n, x in enumerate(lst):
        if n % 2 == 0:
            yield x, ''
        else:
            yield x, 'gray'



