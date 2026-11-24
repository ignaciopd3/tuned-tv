#!/usr/bin/env python3
"""Vectores del protocolo LAN de Tuya (3.3 y 3.5) para las pruebas del complemento Casa.

Hace las tramas con el propio tinytuya, con una clave y un id falsos y con el azar y la hora fijos, así que la
salida es siempre la misma. Las pruebas de Java comprueban que Casa empaqueta exactamente los mismos bytes y que
entiende las respuestas.
Uso (con el Python de ~/Documents/casa-tuya/venv):
  casa_vectors.py > ../cleanyourtv/addons/casa/app/src/test/resources/vectors.json
"""
import hmac
import json
import struct
import sys
from hashlib import sha256
from unittest import mock

import tinytuya
from tinytuya.core import command_types as CT, header as H
from tinytuya.core.crypto_helper import AESCipher
from tinytuya.core.message_helper import TuyaMessage, pack_message, unpack_message

KEY = b"0123456789abcdef"   # falsa
DEV = "fakedevice000001"    # falso
T = 1700000000


def fixed_urandom():
    calls = {"n": 0}

    def urandom(n):
        calls["n"] += 1
        return bytes((calls["n"] * 17 + i) & 0xFF for i in range(n))
    return urandom


def frame_info(frame, key=None):
    """seq, cmd, IV y texto en claro de una trama que envía el cliente."""
    if frame[:4] == H.PREFIX_6699_BIN:
        _, seq, cmd, _ = struct.unpack(">HIII", frame[4:18])
        raw = unpack_message(frame, hmac_key=key, no_retcode=True).payload
        return {"seq": seq, "cmd": cmd, "iv": frame[18:30].hex(), "raw": raw.hex(), "frame": frame.hex()}
    seq, cmd = struct.unpack(">II", frame[4:12])
    return {"seq": seq, "cmd": cmd, "frame": frame.hex()}


def frame_info34(frame, key):
    """seq, cmd y texto en claro (sin el relleno PKCS7) de una trama 3.4 que envía el cliente."""
    seq, cmd, length = struct.unpack(">III", frame[4:16])
    enc = frame[16:16 + length - 36]
    raw = AESCipher(key).decrypt(enc, False, decode_text=False)
    return {"seq": seq, "cmd": cmd, "raw": raw.hex(), "frame": frame.hex()}


def cloud_vectors():
    """Firma y cifrado de la nube con las funciones del SDK oficial (tuya_sharing.customerapi), con valores fijos."""
    import base64
    from hashlib import md5
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from tuya_sharing import customerapi as ca
    rid, refresh, access, t = "11111111-2222-3333-4444-555555555555", "refreshTokenFake", "accessTokenFake", "1700000000000"
    hash_key = md5((rid + refresh).encode()).hexdigest()
    secret = ca._secret_generating(rid, "", hash_key)
    nonce = "ABCDEFGHJKMN"
    with mock.patch.object(ca, "_random_nonce", return_value=nonce):
        query = ca._aes_gcm_encrypt(ca._form_to_json({"devIds": "a1,b2"}), secret).decode()
        body = ca._aes_gcm_encrypt(ca._form_to_json({"linkId": "tuya-device-sharing-sdk-python.x"}), secret).decode()
    headers = {"X-appKey": CLIENT_ID, "X-requestId": rid, "X-sid": "", "X-time": t, "X-token": access}
    plain = '{"success":true,"items":[1,2]}'
    rnonce = b"0123456789ab"
    result = base64.b64encode(rnonce + AESGCM(secret.encode()).encrypt(rnonce, plain.encode(), None)).decode()
    return {"rid": rid, "refreshToken": refresh, "accessToken": access, "time": t, "clientId": CLIENT_ID,
            "hashKey": hash_key, "secret": secret, "nonce": nonce,
            "queryJson": '{"devIds":"a1,b2"}', "queryEnc": query,
            "bodyJson": '{"linkId":"tuya-device-sharing-sdk-python.x"}', "bodyEnc": body,
            "signGet": ca._restful_sign(hash_key, query, "", headers),
            "signPost": ca._restful_sign(hash_key, "", body, headers),
            "result": result, "resultPlain": plain}


CLIENT_ID = "HA_3y9q4ak7g4ephrvke"


def main():
    out = {"key": KEY.decode(), "devId": DEV, "t": T}
    with mock.patch("time.time", return_value=T), mock.patch("os.urandom", side_effect=fixed_urandom()):
        d3 = tinytuya.OutletDevice(DEV, "127.0.0.1", KEY.decode(), version=3.3)
        for name, cmd, data in (("v33_control", CT.CONTROL, {"1": True}), ("v33_query", CT.DP_QUERY, None)):
            p = d3.generate_payload(cmd, data)
            out[name] = dict(frame_info(d3._encode_message(p)), json=p.payload.decode())
        resp = b'{"devId":"fakedevice000001","dps":{"1":true,"9":0}}'
        msg = TuyaMessage(7, CT.DP_QUERY, None, struct.pack(">I", 0) + AESCipher(KEY).encrypt(resp, False), 0, True,
                          H.PREFIX_55AA_VALUE, None)
        out["v33_response"] = {"frame": pack_message(msg).hex(), "json": resp.decode()}

        d5 = tinytuya.OutletDevice(DEV, "127.0.0.1", KEY.decode(), version=3.5)
        f1 = d5._encode_message(d5._negotiate_session_key_generate_step_1())
        remote = bytes(range(0x80, 0x90))
        m2 = TuyaMessage(1, CT.SESS_KEY_NEG_RESP, 0, remote + hmac.new(KEY, d5.local_nonce, sha256).digest(), 0, True,
                         H.PREFIX_6699_VALUE, bytes(range(0x40, 0x4C)))
        f2 = pack_message(m2, hmac_key=KEY)
        f3 = d5._encode_message(d5._negotiate_session_key_generate_step_3(unpack_message(f2, hmac_key=KEY)))
        d5._negotiate_session_key_generate_finalize()
        session = d5.local_key
        p4 = d5.generate_payload(CT.CONTROL, {"1": True})
        f4 = d5._encode_message(p4)
        resp5 = b'{"protocol":4,"t":1700000000,"data":{"dps":{"1":true}}}'
        m5 = TuyaMessage(2, CT.STATUS, 0, H.PROTOCOL_35_HEADER + resp5, 0, True, H.PREFIX_6699_VALUE,
                         bytes(range(0x50, 0x5C)))
        out["v35"] = {
            "localNonce": d5.local_nonce.hex(), "remoteNonce": remote.hex(), "sessionKey": session.hex(),
            "step1": frame_info(f1, KEY), "step2": {"frame": f2.hex()}, "step3": frame_info(f3, KEY),
            "control": dict(frame_info(f4, session), json=p4.payload.decode()),
            "response": {"frame": pack_message(m5, hmac_key=session).hex(), "json": resp5.decode()},
        }
        d4 = tinytuya.OutletDevice(DEV, "127.0.0.1", KEY.decode(), version=3.4)
        g1 = d4._encode_message(d4._negotiate_session_key_generate_step_1())
        remote4 = bytes(range(0x90, 0xA0))
        enc2 = AESCipher(KEY).encrypt(remote4 + hmac.new(KEY, d4.local_nonce, sha256).digest(), False)
        g2 = pack_message(TuyaMessage(1, CT.SESS_KEY_NEG_RESP, None, struct.pack(">I", 0) + enc2, 0, True,
                                      H.PREFIX_55AA_VALUE, None), hmac_key=KEY)
        g3 = d4._encode_message(d4._negotiate_session_key_generate_step_3(unpack_message(g2, hmac_key=KEY)))
        d4._negotiate_session_key_generate_finalize()
        session4 = d4.local_key
        q = d4.generate_payload(CT.DP_QUERY)
        g4 = d4._encode_message(q)
        hb = d4.generate_payload(CT.HEART_BEAT)
        g5 = d4._encode_message(hb)
        push = b'{"protocol":4,"t":1700000000,"data":{"dps":{"2":"alarm"}}}'
        enc6 = AESCipher(session4).encrypt(H.PROTOCOL_34_HEADER + push, False)
        g6 = pack_message(TuyaMessage(3, CT.STATUS, None, struct.pack(">I", 0) + enc6, 0, True, H.PREFIX_55AA_VALUE,
                                      None), hmac_key=session4)
        out["v34"] = {
            "localNonce": d4.local_nonce.hex(), "remoteNonce": remote4.hex(), "sessionKey": session4.hex(),
            "step1": frame_info34(g1, KEY), "step2": {"frame": g2.hex()}, "step3": frame_info34(g3, KEY),
            "query": frame_info34(g4, session4), "heartbeat": frame_info34(g5, session4),
            "status": {"frame": g6.hex(), "json": push.decode()},
        }
    out["cloud"] = cloud_vectors()
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
