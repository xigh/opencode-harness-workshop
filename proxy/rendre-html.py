#!/usr/bin/env python3
"""Rend la conversation d'une étape (journal du proxy) en page HTML colorée, autonome.

Usage : rendre-html.py journal/appels.jsonl 04-boucle journal/conversations/04-boucle.html
Chaque appel au modèle est une carte : messages nouveaux depuis l'appel précédent du même fil, puis la réponse.
Prompt système et outils repliables, raisonnement replié. Rien n'est tronqué.
Écrit par Claude (outillage), pas par OpenCode.
"""
import html, json, sys


def masquer(s):
    """Retire de l'affichage la liste des compétences du poste injectée par OpenCode et le nom du compte local."""
    import re as _re
    if not isinstance(s, str):
        return s
    s = _re.sub(r'<available_skills>.*?</available_skills>', '<available_skills>\n[compétences installées sur le poste : masquées pour la projection]\n</available_skills>', s, flags=_re.S)
    return _re.sub(r'/Users/[^/\s"]+/', '~/', s)

def esc(s):
    return html.escape(s or '')


def masquer_tout(x):
    """masquer() appliqué à toutes les chaînes d'une entrée du journal, avant toute mise en forme."""
    if isinstance(x, str):
        return masquer(x)
    if isinstance(x, list):
        return [masquer_tout(v) for v in x]
    if isinstance(x, dict):
        return {k: masquer_tout(v) for k, v in x.items()}
    return x

def contenu(c):
    if c is None:
        return ''
    if isinstance(c, str):
        return c
    return '\n'.join(p.get('text', json.dumps(p, ensure_ascii=False)) for p in c)

def joli_json(s):
    try:
        return json.dumps(json.loads(s), ensure_ascii=False, indent=2)
    except Exception:
        return s or ''

def message(m):
    r = m.get('role', '?')
    h = [f'<div class="msg {r}"><div class="role">{r}']
    if m.get('tool_call_id'):
        h.append(f' <span class="id">← {esc(m["tool_call_id"])}</span>')
    h.append('</div>')
    if m.get('reasoning_content'):
        h.append(f'<details class="raison"><summary>raisonnement ({len(m["reasoning_content"])} car.)</summary><pre>{esc(m["reasoning_content"])}</pre></details>')
    t = contenu(m.get('content'))
    if t:
        if r == 'tool':
            t = joli_json(t)
        h.append(f'<pre>{esc(t)}</pre>')
    for tc in m.get('tool_calls') or []:
        f = tc.get('function') or tc
        h.append(f'<div class="appel">→ <b>{esc(f.get("name"))}</b> <span class="id">{esc(tc.get("id"))}</span>'
                 f'<pre>{esc(joli_json(f.get("arguments")))}</pre></div>')
    h.append('</div>')
    return ''.join(h)

def main(src, etape, dst):
    appels = [masquer_tout(e) for e in map(json.loads, open(src)) if e.get('etape') == etape]
    cartes, prec, sys_vus, outils_vus = [], {}, set(), set()
    tot_in = tot_out = 0
    for e in appels:
        req = e['requete'] if isinstance(e['requete'], dict) else {}
        msgs = req.get('messages', [])
        sig = tuple(t['function']['name'] for t in req.get('tools', []))
        fil = 'opencode' if 'bash' in sig else 'programme'
        rep = e.get('reponse_reconstituee')
        if rep is None and isinstance(e.get('reponse'), dict):
            ch = (e['reponse'].get('choices') or [{}])[0]
            rep = dict(ch.get('message', {}), finish_reason=ch.get('finish_reason'), usage=e['reponse'].get('usage'))
        rep = rep or {}
        u = rep.get('usage') or {}
        tot_in += u.get('prompt_tokens') or 0
        tot_out += u.get('completion_tokens') or 0
        c = [f'<section class="carte {fil}"><header><span class="n">appel {e["n"]}</span>'
             f'<span class="fil">{"OpenCode" if fil == "opencode" else "programme écrit par OpenCode"}</span>'
             f'<span>{e["debut"][11:]}</span><span>{e["duree_s"]} s</span><span>{len(msgs)} messages</span>'
             f'<span>entrée {u.get("prompt_tokens")} tk</span><span>sortie {u.get("completion_tokens")} tk</span></header>']
        if e.get('erreur'):
            c.append(f'<div class="err">erreur proxy : {esc(e["erreur"])}</div>')
        if req.get('tools'):
            if sig not in outils_vus:
                outils_vus.add(sig)
                c.append(f'<details class="outils"><summary>outils déclarés ({len(sig)}) : {esc(", ".join(sig))}</summary>'
                         f'<pre>{esc(json.dumps(req["tools"], ensure_ascii=False, indent=2))}</pre></details>')
            else:
                c.append(f'<div class="note">outils : {esc(", ".join(sig))} (mêmes que plus haut)</div>')
        debut = 0
        if msgs and msgs[0].get('role') == 'system':
            s = contenu(msgs[0].get('content'))
            if s not in sys_vus:
                sys_vus.add(s)
                c.append(f'<details class="msg system"><summary>prompt système ({len(s)} caractères)</summary><pre>{esc(s)}</pre></details>')
            else:
                c.append('<div class="note">prompt système : identique à plus haut</div>')
            debut = 1
        p = prec.get((fil, sig), [])
        if p and msgs[:len(p)] == p:
            c.append(f'<div class="note">{len(p) - debut} messages précédents renvoyés tels quels (le fil grossit)</div>')
            debut = len(p)
        c += [message(m) for m in msgs[debut:]]
        c.append(f'<div class="rep-titre">réponse du modèle · fin : <b>{esc(rep.get("finish_reason"))}</b></div>')
        c.append(message({'role': 'assistant réponse', 'content': rep.get('content'), 'reasoning_content': rep.get('reasoning_content'),
                          'tool_calls': [{'id': t.get('id'), 'function': {'name': t.get('name'), 'arguments': t.get('arguments')}}
                                         for t in rep.get('tool_calls') or []]}))
        c.append('</section>')
        cartes.append(''.join(c))
        prec[(fil, sig)] = msgs
    page = f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Étape {esc(etape)}</title><style>
:root{{--fond:#f6f7f9;--carte:#fff;--txt:#1d2330;--doux:#667085;--bord:#dfe3ea;
--sys:#eef0f4;--user:#e6f0ff;--asst:#e7f7ec;--tool:#fff3e0;--appel:#f3e8ff;--raison:#f7f7f2}}
@media (prefers-color-scheme:dark){{:root{{--fond:#12151b;--carte:#1a1f27;--txt:#e4e7ec;--doux:#98a2b3;--bord:#2c333f;
--sys:#232833;--user:#16263f;--asst:#15301f;--tool:#3a2a12;--appel:#2c1d42;--raison:#24241c}}}}
body{{margin:0;background:var(--fond);color:var(--txt);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:16px}}
h1{{font-size:22px;margin:8px 0}} .resume{{color:var(--doux);margin-bottom:16px}}
.carte{{background:var(--carte);border:1px solid var(--bord);border-radius:10px;margin:14px 0;padding:10px 14px;border-left:6px solid #3b82f6}}
.carte.programme{{border-left-color:#f59e0b}}
header{{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--doux);margin-bottom:8px}}
header .n{{font-weight:700;color:var(--txt)}} header .fil{{font-weight:600}}
.msg{{border-radius:8px;padding:6px 10px;margin:6px 0}}
.msg.system{{background:var(--sys)}} .msg.user{{background:var(--user)}}
.msg.assistant,.msg[class*="réponse"]{{background:var(--asst)}} .msg.tool{{background:var(--tool)}}
.role{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--doux)}}
.appel{{background:var(--appel);border-radius:6px;padding:4px 8px;margin:4px 0}}
.raison{{background:var(--raison);border-radius:6px;padding:2px 8px;margin:4px 0;font-size:13px}}
pre{{white-space:pre-wrap;word-break:break-word;margin:4px 0;font:13px/1.4 ui-monospace,Menlo,monospace}}
summary{{cursor:pointer;color:var(--doux);font-size:13px}} .note{{font-size:12px;color:var(--doux);font-style:italic;margin:4px 0}}
.rep-titre{{font-size:12px;color:var(--doux);margin-top:10px}} .id{{font-size:11px;color:var(--doux)}}
.err{{color:#dc2626}} details.outils{{margin:4px 0}}
.legende span{{display:inline-block;padding:2px 8px;border-radius:6px;margin-right:6px;font-size:12px}}
</style></head><body><main>
<h1>Étape {esc(etape)} : conversation complète</h1>
<div class="resume">{len(appels)} appels au modèle · {tot_in} tokens envoyés · {tot_out} tokens générés · source : <code>appels.jsonl</code> (n° {appels[0]["n"]} à {appels[-1]["n"]})</div>
<div class="legende"><span style="background:var(--sys)">système</span><span style="background:var(--user)">utilisateur</span><span style="background:var(--asst)">assistant</span><span style="background:var(--appel)">appel d'outil</span><span style="background:var(--tool)">résultat d'outil</span><span style="background:var(--raison)">raisonnement</span> · bord bleu : OpenCode · bord orange : programme écrit par OpenCode</div>
{''.join(cartes)}
</main></body></html>'''
    open(dst, 'w').write(masquer(page))
    print(dst, len(appels), 'appels')

if __name__ == '__main__':
    main(*sys.argv[1:4])
