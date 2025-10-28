
import json, re, urllib.request

MECHANIC_WORDS = {
 'flying','first strike','double strike','menace','deathtouch','lifelink','trample','reach','vigilance','haste',
 'hexproof','ward','defender','flash','equip','scry','kicker','cycling','exploit','proliferate','exile',
 'token','draw','tap','untap','destroy','counter','sacrifice','create','add','damage'
}

def _clean_name(n:str)->str:
    if not n: return n
    n = re.sub(r'[;:\n\r]+',' ', n).strip().title()
    words = n.split()
    if len(words) > 4: n = ' '.join(words[:4])
    low = n.lower()
    if any(w in low for w in MECHANIC_WORDS):
        n = 'Nameless'
    return n

def _req(url, body, timeout=60.0):
    data = json.dumps(body).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))

def name_art_flavor(set_context:str, card_text:str, mv:int, pt:str=None, subtypes:str="", model:str='llama3', host:str='http://localhost:11434'):
    sys = """You generate flavorful elements for a custom Magic-style card.
- OUTPUT: JSON only with keys exactly: name, art, flavor.
- Do NOT repeat rules text, mana, or keywords in the name.
- NAME: 1–4 words, Title Case, evocative, no punctuation like ';' or ':'.
- ART: 1–2 sentences, concise brief. No mechanics terms.
- FLAVOR: One quoted line <= 140 chars, not rules.
If unsure, return empty strings but keep valid JSON."""
    user = f"""Set description:
{set_context}

Mechanical context (do not quote these in output):
Mana Value: {mv}
{('Power/Toughness: '+pt) if pt else ''}
Subtype: {subtypes}
Rules Text:
{card_text}

Return JSON ONLY: {{\"name\":\"...\",\"art\":\"...\",\"flavor\":\"...\"}}"""
    url = host.rstrip('/') + '/api/generate'
    body = {"model": model, "prompt": sys + "\n\n" + user, "stream": False}
    try:
        js = _req(url, body)
        resp = js.get("response",""
        )
        start = resp.find('{'); end = resp.rfind('}')+1
        o = json.loads(resp[start:end])
        name = _clean_name((o.get("name","") or "").strip())
        art = (o.get("art","") or "").replace('\n',' ').strip()
        flavor = (o.get("flavor","") or "").replace('\n',' ').strip()
        if not flavor.startswith('"'): flavor = '"'+flavor
        if not flavor.endswith('"'): flavor = flavor + '"'
        if not name: name = "Nameless"
        if not art: art = "A mood-rich fantasy scene matching the set themes."
        if not flavor or flavor == '""': flavor = "\"A whisper from the set's heart.\""
        return {"name": name, "art": art, "flavor": flavor}
    except Exception:
        return {"name":"Nameless","art":"A mood-rich fantasy scene matching the set themes.","flavor":"\"A whisper from the set's heart.\""}
