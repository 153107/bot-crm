import subprocess
import time
import sys
import os

os.chdir(r'C:\Users\jf102696\Downloads\growth-bot')
log = open(r'C:\Users\jf102696\Downloads\growth-bot\service.log', 'a', encoding='utf-8')

while True:
    log.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Iniciando bot...\n')
    log.flush()
    proc = subprocess.run(
        [sys.executable, 'app.py'],
        cwd=r'C:\Users\jf102696\Downloads\growth-bot',
        stdout=log,
        stderr=log
    )
    log.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] Bot encerrou (code {proc.returncode}). Reiniciando em 10s...\n')
    log.flush()
    time.sleep(10)
