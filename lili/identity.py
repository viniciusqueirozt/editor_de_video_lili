"""Request-bound identity assertions for a future trusted gateway integration.

The browser must never receive the transport key or mint these headers. This
module does not validate portal passwords/sessions and is not enabled by main().
"""
import hashlib
import hmac
import json
import re
import secrets
import threading
import time
from .access import Principal

_FIELDS=("X-Lili-Identity","X-Lili-Identity-Time","X-Lili-Identity-Nonce","X-Lili-Identity-Signature")

def _configuration(key,audience):
    if not isinstance(key,bytes) or len(key)<32:
        raise ValueError("A transport key of at least 32 bytes is required")
    if not isinstance(audience,str) or re.fullmatch(r"[A-Za-z0-9_-]{16,128}",audience) is None:
        raise ValueError("A per-instance audience is required")

def _payload(audience,subject,stamp,nonce,method,target,length,content_type):
    if method not in ("GET","HEAD","POST","PUT") or not isinstance(target,str) or not target.startswith("/") or target.startswith("//") or len(target)>4096 or any(c in target for c in "\r\n"):
        raise ValueError("Invalid request target")
    if isinstance(length,bool) or not isinstance(length,int) or not 0<=length<=2*1024**3:
        raise ValueError("Invalid request length")
    if not isinstance(content_type,str) or len(content_type)>200 or any(c in content_type for c in "\r\n"):
        raise ValueError("Invalid content type")
    return json.dumps(["lili-local-identity-v1",audience,subject,stamp,nonce,method,target,length,content_type],separators=(",",":"),ensure_ascii=True).encode()

class IdentitySigner:
    def __init__(self,key,audience,clock=time.time):
        _configuration(key,audience)
        self._key,self.audience,self.clock=key,audience,clock

    def headers(self,principal,method,target,*,length=0,content_type=""):
        if not isinstance(principal,Principal):raise ValueError("A previously authenticated Principal is required")
        stamp=str(int(self.clock()));nonce=secrets.token_hex(16)
        payload=_payload(self.audience,principal.subject,stamp,nonce,method,target,length,content_type)
        signature=hmac.new(self._key,payload,hashlib.sha256).hexdigest()
        return dict(zip(_FIELDS,(principal.subject,stamp,nonce,signature)))

class IdentityVerifier:
    def __init__(self,key,audience,clock=time.time,*,ttl=30,capacity=4096):
        _configuration(key,audience)
        if type(ttl) is not int or not 1<=ttl<=60 or type(capacity) is not int or capacity<1:
            raise ValueError("Invalid assertion limits")
        self._key,self.audience,self.clock=key,audience,clock
        self.ttl,self.capacity=ttl,capacity
        self._seen={};self._lock=threading.Lock()

    def __call__(self,request):
        # Reject missing/duplicate assertion fields, never accept a bare user ID.
        values=[request.headers.get_all(name,[]) for name in _FIELDS]
        if any(len(items)!=1 for items in values):return None
        subject,stamp,nonce,signature=[items[0] for items in values]
        try:
            principal=Principal(subject)
            if re.fullmatch(r"[0-9]{1,12}",stamp) is None or re.fullmatch(r"[a-f0-9]{32}",nonce) is None or re.fullmatch(r"[a-f0-9]{64}",signature) is None:return None
            now=int(self.clock());issued=int(stamp)
            if issued>now+5 or now-issued>self.ttl:return None
            sizes=request.headers.get_all("Content-Length",[])
            types=request.headers.get_all("Content-Type",[])
            if len(sizes)>1 or len(types)>1:return None
            size=sizes[0] if sizes else "0"
            if re.fullmatch(r"[0-9]{1,12}",size) is None:return None
            payload=_payload(self.audience,subject,stamp,nonce,request.command,request.path,int(size),types[0] if types else "")
            expected=hmac.new(self._key,payload,hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature,expected):return None
        except (ValueError,TypeError):return None
        with self._lock:
            self._seen={n:expiry for n,expiry in self._seen.items() if expiry>now}
            if nonce in self._seen or len(self._seen)>=self.capacity:return None
            self._seen[nonce]=issued+self.ttl+1
        return principal
