#!/usr/bin/env python3
"""Rend le journal du proxy (appels.jsonl) en conversations Markdown lisibles, une par étape.

Pour chaque étape : le prompt système et la liste des outils une seule fois (en entier), puis appel par appel
les messages nouveaux par rapport à l'appel précédent du même fil, la réponse (raisonnement, texte, appels d'outils),
les tokens et la durée. Les appels faits par le programme écrit par OpenCode (et non par OpenCode lui-même)
sont repérés à leurs outils différents et rendus comme un fil séparé. Rien n'est tronqué : le JSONL reste
la référence, ce rendu sert à lire.

Usage : rendre-journal.py journal/appels.jsonl journal/conversations/
Écrit par Claude (outillage), pas par OpenCode.
"""
import json, os, sys
from collections import defaultdict



def masquer(s):
    """Retire de l'affichage la liste des compétences du poste injectée par OpenCode et le nom du compte local."""
    import re as _re
    if not isinstance(s, str):
        return s
    s = _re.sub(r'<available_skills>.*?</available_skills>', '<available_skills>\n[compétences installées sur le poste : masquées pour la projection]\n</available_skills>', s, flags=_re.S)
    return _re.sub(r'/Users/[^/\s"]+/', '~/', s)

def texte_contenu(c):
    if c is None:
        return ''
    if isinstance(c, str):
        return c
    return '\n'.join(p.get('text', json.dumps(p, ensure_ascii=False)) for p in c)



def masquer_tout(x):
    """masquer() appliqué à toutes les chaînes d'une entrée du journal, avant toute mise en forme."""
    if isinstance(x, str):
        return masquer(x)
    if isinstance(x, list):
        return [masquer_tout(v) for v in x]
    if isinstance(x, dict):
        return {k: masquer_tout(v) for k, v in x.items()}
    return x

def bloc(t, langue=''):
    t = t if t.endswith('\n') else t + '\n'
    fence = '````' if '```' in t else '```'
    return f'{fence}{langue}\n{t}{fence}\n'


def rendre_message(m):
    r = m.get('role')
    out = [f'**{r}**' + (f' (tool_call_id `{m["tool_call_id"]}`)' if m.get('tool_call_id') else '') + '\n']
    if m.get('reasoning_content'):
        out.append('_raisonnement :_\n' + bloc(m['reasoning_content']))
    t = texte_contenu(m.get('content'))
    if t:
        out.append(bloc(t))
    for tc in m.get('tool_calls') or []:
        f = tc.get('function', {})
        out.append(f'→ appel d\'outil `{f.get("name")}` (id `{tc.get("id")}`)\n' + bloc(f.get('arguments', ''), 'json'))
    return '\n'.join(out)


def signature(req):
    return tuple(t['function']['name'] for t in req.get('tools', []) if 'function' in t)


def main(src, dst):
    os.makedirs(dst, exist_ok=True)
    par_etape = defaultdict(list)
    for l in open(src):
        e = masquer_tout(json.loads(l))
        par_etape[e.get('etape') or 'sans-etape'].append(e)
    for etape, appels in par_etape.items():
        o = [f'# Conversation de l\'étape {etape}\n',
             f'{len(appels)} appels au modèle. Source brute : `appels.jsonl` (entrées n° {appels[0]["n"]} à {appels[-1]["n"]}).\n']
        vus_sys, vus_outils, precedent = set(), set(), {}
        for e in appels:
            req = e['requete'] if isinstance(e['requete'], dict) else {}
            msgs = req.get('messages', [])
            sig = signature(req)
            fil = 'OpenCode' if 'bash' in sig else ('programme écrit par OpenCode' if msgs else 'autre')
            rep = e.get('reponse_reconstituee')
            if rep is None and isinstance(e.get('reponse'), dict):
                ch = (e['reponse'].get('choices') or [{}])[0]
                rep = dict(ch.get('message', {}), finish_reason=ch.get('finish_reason'), usage=e['reponse'].get('usage'),
                           timings=e['reponse'].get('timings'))
            rep = rep or {}
            u = rep.get('usage') or {}
            o.append(f'\n---\n\n## Appel {e["n"]} ({fil}) : {e["debut"]}, {e["duree_s"]} s, '
                     f'{len(msgs)} messages, entrée {u.get("prompt_tokens")} tokens, sortie {u.get("completion_tokens")} tokens\n')
            if e.get('erreur'):
                o.append(f'⚠️ erreur côté proxy : `{e["erreur"]}`\n')
            params = {k: v for k, v in req.items() if k not in ('messages', 'tools')}
            if params:
                o.append('Paramètres :\n' + bloc(json.dumps(params, ensure_ascii=False, indent=1), 'json'))
            if req.get('tools') and sig not in vus_outils:
                vus_outils.add(sig)
                o.append(f'### Outils déclarés ({len(sig)}) : {", ".join(sig)}\n')
                o.append(bloc(json.dumps(req['tools'], ensure_ascii=False, indent=1), 'json'))
            debut = 0
            if msgs and msgs[0].get('role') == 'system':
                s = texte_contenu(msgs[0].get('content'))
                if s not in vus_sys:
                    vus_sys.add(s)
                    o.append(f'### Prompt système ({len(s)} caractères)\n' + bloc(s))
                else:
                    o.append('_Prompt système : identique à celui affiché plus haut._\n')
                debut = 1
            prec = precedent.get((fil, sig), [])
            if prec and msgs[:len(prec)] == prec:
                o.append(f'_{len(prec) - debut} messages précédents repris tels quels, nouveaux messages :_\n')
                debut = len(prec)
            for m in msgs[debut:]:
                o.append(rendre_message(m))
            o.append('### Réponse du modèle' + (f' (fin : `{rep.get("finish_reason")}`)' if rep.get('finish_reason') else '') + '\n')
            o.append(rendre_message({'role': 'assistant', 'content': rep.get('content'),
                                     'reasoning_content': rep.get('reasoning_content'),
                                     'tool_calls': [{'id': t.get('id'), 'function': {'name': t.get('name'), 'arguments': t.get('arguments')}}
                                                    if 'function' not in t else t for t in rep.get('tool_calls') or []]}))
            precedent[(fil, sig)] = msgs
        nom = os.path.join(dst, f'{etape}.md')
        open(nom, 'w').write(masquer('\n'.join(o)))
        print(nom, len(appels), 'appels')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
