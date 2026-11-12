#!/usr/bin/env python3
import json
import os
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

PORT = int(os.environ.get('PORT', 8095))
MODEL_PATH = '/home/ucab-spark1/Documents/lab6/salidas/modelo_fusionado'

print(f'[PYTORCH SERVER] Cargando modelo en GPU Blackwell desde {MODEL_PATH}...')
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
    device_map='cuda'
)
print(f'[PYTORCH SERVER] Listo en GPU. Arrancando servidor en puerto {PORT}...')

HTML = '''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Maestro Yiyo - PyTorch Nativo</title>
<style>
body { background:#0f172a; color:#f8fafc; font-family:sans-serif; margin:0; padding:20px; display:flex; flex-direction:column; height:90vh; }
#chat { flex:1; overflow-y:auto; border:1px solid #334155; padding:15px; border-radius:8px; margin-bottom:15px; background:#1e293b; }
.msg { margin:10px 0; padding:10px 14px; border-radius:8px; max-width:80%; line-height:1.5; }
.user { background:#0284c7; align-self:flex-end; margin-left:auto; }
.bot { background:#334155; border-left:4px solid #10b981; }
form { display:flex; gap:10px; }
input { flex:1; padding:12px; background:#0b0f19; border:1px solid #334155; border-radius:6px; color:#fff; font-size:16px; }
button { background:#10b981; color:#fff; border:none; padding:0 25px; border-radius:6px; font-weight:bold; cursor:pointer; font-size:16px; }
button:disabled { opacity:0.5; }
.header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.badge { background:#065f46; color:#34d399; padding:4px 8px; border-radius:4px; font-size:12px; }
</style>
</head>
<body>
<div class="header">
  <h2>🔧 Maestro Yiyo (PyTorch Puro / Sin llama.cpp)</h2>
  <span class="badge">NVIDIA Blackwell GB10 · bfloat16</span>
</div>
<div id="chat">
  <div class="msg bot">¡Epa mi pana! Aquí estás corriendo directo en PyTorch puro en la GPU del Spark. Cero llama.cpp, cero truncamiento raro. ¿Qué falla le ves al carro o al sistema?</div>
</div>
<form onsubmit="send(event)">
  <input id="inp" placeholder="Escribe tu mensaje..." autocomplete="off"/>
  <button id="btn">Enviar</button>
</form>
<script>
let hist = [];
async function send(e) {
  e.preventDefault();
  let inp = document.getElementById('inp');
  let txt = inp.value.trim();
  if(!txt) return;
  inp.value = '';
  addMsg('user', txt);
  hist.push({role:'user', content:txt});
  let btn = document.getElementById('btn');
  btn.disabled = true;
  try {
    let r = await fetch('/v1/chat/completions', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({messages:hist, temperature:0.7, max_tokens:250})
    });
    let d = await r.json();
    let ans = d.choices[0].message.content;
    hist.push({role:'assistant', content:ans});
    addMsg('bot', ans);
  } catch(err) {
    addMsg('bot', 'Error: ' + err);
  } finally {
    btn.disabled = false;
    inp.focus();
  }
}
function addMsg(cls, txt) {
  let c = document.getElementById('chat');
  let d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.innerText = txt;
  c.appendChild(d);
  c.scrollTop = c.scrollHeight;
}
</script>
</body>
</html>'''

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ['/', '/index.html']:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML.encode('utf-8'))
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok","backend":"pytorch"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/v1/chat/completions':
            l = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(l).decode('utf-8'))
            msgs = data.get('messages', [])
            temp = float(data.get('temperature', 0.7))
            max_t = int(data.get('max_tokens', 250))
            
            prompt = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(prompt, return_tensors='pt').to('cuda')
            
            with torch.no_grad():
                out = model.generate(**inputs, max_new_tokens=max_t, temperature=temp, do_sample=True, repetition_penalty=1.15)
            
            gen = tokenizer.decode(out[0][len(inputs.input_ids[0]):], skip_special_tokens=True).strip()
            
            res = {
                'choices': [{'message': {'role': 'assistant', 'content': gen}}]
            }
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(res).encode('utf-8'))

class Server(ThreadingMixIn, HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    srv = Server(('0.0.0.0', PORT), Handler)
    print(f'Server listening on port {PORT}')
    srv.serve_forever()
