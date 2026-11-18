#!/usr/bin/env python3
"""Proxy de journalisation entre un client (OpenCode, le harnais) et un serveur compatible OpenAI (llama-server).

Chaque échange est écrit en entier dans un fichier JSONL : la requête telle qu'envoyée (prompt système, historique,
outils), la réponse brute (y compris chaque morceau du streaming SSE) et la réponse reconstituée (texte, raisonnement,
appels d'outils, compteurs de tokens). Rien n'est tronqué.

Usage : proxy-journal.py --amont http://127.0.0.1:8080 --port 8800 --journal journal/appels.jsonl
L'étape courante (pour retrouver les appels d'un prompt donné) se lit dans le fichier indiqué par --etape, s'il existe.

Écrit par Claude (outillage), pas par OpenCode.
"""
import argparse, json, threading, time, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

verrou = threading.Lock()
compteur = 0


def reconstituer(morceaux):
    """Recompose un message à partir des morceaux SSE de chat/completions."""
    texte, raisonnement, appels, fin, usage, timings = [], [], {}, None, None, None
    for m in morceaux:
        for ch in m.get('choices', []):
            d = ch.get('delta', {})
            if d.get('content'):
                texte.append(d['content'])
            if d.get('reasoning_content'):
                raisonnement.append(d['reasoning_content'])
            for tc in d.get('tool_calls') or []:
                a = appels.setdefault(tc.get('index', 0), {'id': None, 'name': '', 'arguments': ''})
                a['id'] = tc.get('id') or a['id']
                f = tc.get('function') or {}
                a['name'] += f.get('name') or ''
                a['arguments'] += f.get('arguments') or ''
            fin = ch.get('finish_reason') or fin
        usage = m.get('usage') or usage
        timings = m.get('timings') or timings
    return {'content': ''.join(texte), 'reasoning_content': ''.join(raisonnement),
            'tool_calls': [appels[k] for k in sorted(appels)], 'finish_reason': fin,
            'usage': usage, 'timings': timings}


class Relais(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _relayer(self):
        global compteur
        n = int(self.headers.get('Content-Length') or 0)
        corps = self.rfile.read(n) if n else b''
        t0 = time.time()
        with verrou:
            compteur += 1
            num = compteur
        etape = ''
        try:
            etape = open(A.etape).read().strip()
        except OSError:
            pass
        entetes = {k: v for k, v in self.headers.items() if k.lower() not in ('host', 'content-length', 'accept-encoding', 'connection')}
        req = urllib.request.Request(A.amont + self.path, data=corps if corps else None, method=self.command, headers=entetes)
        morceaux, lignes, erreur = [], [], None
        try:
            self._echanger(req, morceaux, lignes)
        except Exception as e:  # client parti, serveur coupé : on journalise quand même
            erreur = repr(e)
        statut, sse, brut = self._statut, self._sse, self._brut
        try:
            requete = json.loads(corps) if corps else None
        except ValueError:
            requete = corps.decode('utf-8', 'replace')
        entree = {'n': num, 'etape': etape, 'debut': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t0)),
                  'duree_s': round(time.time() - t0, 3), 'methode': self.command, 'chemin': self.path,
                  'statut': statut, 'erreur': erreur, 'requete': requete}
        if sse:
            entree['reponse_reconstituee'] = reconstituer(morceaux)
            entree['reponse_sse_brute'] = brut.decode('utf-8', 'replace')
        else:
            try:
                entree['reponse'] = json.loads(brut)
            except ValueError:
                entree['reponse'] = brut.decode('utf-8', 'replace')
        with verrou, open(A.journal, 'a') as f:
            f.write(json.dumps(entree, ensure_ascii=False) + '\n')


    def _echanger(self, req, morceaux, lignes):
        self._statut, self._sse, self._brut = 0, False, b''
        try:
            rep = urllib.request.urlopen(req, timeout=3600)
        except urllib.error.HTTPError as e:
            rep = e
        self._statut = statut = rep.status if hasattr(rep, 'status') else rep.code
        ent_rep = dict(rep.headers.items())
        self._sse = sse = 'text/event-stream' in ent_rep.get('Content-Type', '')
        if not sse:
            self._brut = rep.read()
        self.send_response(statut)
        for k, v in ent_rep.items():
            if k.lower() in ('transfer-encoding', 'content-length', 'connection'):
                continue
            self.send_header(k, v)
        if sse:
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            for ligne in rep:
                lignes.append(ligne)
                self._brut = b''.join(lignes)
                s = ligne.decode('utf-8', 'replace').strip()
                if s.startswith('data:') and s[5:].strip() not in ('', '[DONE]'):
                    try:
                        morceaux.append(json.loads(s[5:]))
                    except ValueError:
                        pass
                self.wfile.write(b'%x\r\n%s\r\n' % (len(ligne), ligne))
                self.wfile.flush()
            self.wfile.write(b'0\r\n\r\n')
        else:
            self.send_header('Content-Length', str(len(self._brut)))
            self.end_headers()
            self.wfile.write(self._brut)

    do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _relayer


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--amont', default='http://127.0.0.1:8080')
    p.add_argument('--port', type=int, default=8800)
    p.add_argument('--journal', default='journal/appels.jsonl')
    p.add_argument('--etape', default='journal/ETAPE')
    A = p.parse_args()
    try:  # numérotation continue après un redémarrage
        compteur = sum(1 for _ in open(A.journal))
    except OSError:
        pass
    print(f'proxy {A.port} -> {A.amont}, journal {A.journal}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', A.port), Relais).serve_forever()
