"""Loopback-only training monitor: python -m uc3m.presentation.training_panel."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from uc3m.application.training.monitor import list_runs


PAGE = '''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MADRL · Entrenamiento local</title>
<style>body{font:16px system-ui;background:#101c2b;color:#e6edf5;max-width:1200px;margin:40px auto;padding:20px}h1{font-size:30px}p{color:#b4c5d8}table{width:100%;border-collapse:collapse;background:#19293e}th,td{text-align:left;padding:14px;border-bottom:1px solid #35445a}button{padding:10px 20px;border:0;background:#55d9b3;color:#10202c;cursor:pointer}small{display:block;margin:20px 0}</style>
<h1>MADRL / Entrenamiento local</h1>
<p>Integridad de corridas y artefactos. No equivale a validación científica ni selección del mejor modelo.</p>
<button id="refresh">Actualizar</button><small id="message" role="status"></small>
<table><thead><tr><th>Corrida</th><th>Estado</th><th>Episodios</th><th>Archivos verificados</th></tr></thead><tbody id="runs"></tbody></table>
<script>
async function refresh(){const message=document.getElementById('message');try{
const response=await fetch('/api/runs');if(!response.ok)throw Error('HTTP');
const runs=await response.json();const body=document.getElementById('runs');body.replaceChildren();
for(const run of runs){const row=document.createElement('tr');for(const value of [run.run_id,run.status,`${run.completed_episodes??'—'} / ${run.target_episodes??'—'}`,run.artifacts_verified?'Sí':'No']){const cell=document.createElement('td');cell.textContent=value;row.append(cell)}body.append(row)}
message.textContent=runs.length?`${runs.length} corridas · actualizado ${new Date().toLocaleTimeString()}`:'Sin corridas registradas';
}catch(error){message.textContent='No se pudo leer el estado; no se presume completitud.'}}
document.getElementById('refresh').onclick=refresh;refresh();setInterval(refresh,15000);
</script></html>'''


def make_server(output_root: Path, *, port: int = 8765):
    root = Path(output_root).resolve()
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                payload, content_type = PAGE.encode('utf-8'), 'text/html; charset=utf-8'
            elif self.path == '/api/runs':
                payload = json.dumps(list_runs(root)).encode('utf-8')
                content_type = 'application/json'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass
    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-root', type=Path, default=Path('outputs/modular_training'))
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    with make_server(args.output_root, port=args.port) as server:
        print(f'MADRL monitor: http://127.0.0.1:{server.server_port}', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
