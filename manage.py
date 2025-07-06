#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from dotenv import dotenv_values
import re
import argparse

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FILE = BASE_DIR / "docker-compose.stack.yml.template"
RENDERED_FILE = BASE_DIR / "docker-compose.stack.yml"

def run(cmd):
    print(f"▶️  {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executant la comanda: {' '.join(cmd)}")
        print(f"🔧 Codi de sortida: {e.returncode}")
        sys.exit(e.returncode)

def help(extra_args=[]):
    print("""
Comandes disponibles:
  build         - Construeix la imatge
  up            - Inicia amb docker-compose
  down          - Atura amb docker-compose
  push          - Puja la imatge
  render        - Substitueix variables i genera YAML final
  stack         - Deploy a docker stack
  stack-down    - Elimina l'stack
  generate      - Genera el fitxer docker-compose per a Swarm
  deploy        - Fa push, genera i desplega amb stack
  clean         - Elimina el fitxer generat
""")

def build(extra_args=[]):
    files = ["-f", env_vars["BASE"], "-f", env_vars["OVERRIDE"]]
    run(["docker", "compose", *files, "build", *extra_args])

def up(extra_args=[]):
    files = ["-f", env_vars["BASE"], "-f", env_vars["OVERRIDE"]]
    mode = env_vars["MODE"].split() if env_vars["MODE"] else []
    run(["docker", "compose", *files, "up", *mode, *extra_args])

def down(extra_args=[]):
    files = ["-f", env_vars["BASE"], "-f", env_vars["OVERRIDE"]]
    run(["docker", "compose", *files, "down", *extra_args])

def push(extra_args=[]):
    files = ["-f", env_vars["BASE"], "-f", env_vars["OVERRIDE"]]
    run(["docker", "compose", *files, "push", *extra_args])

def render(extra_args=[]):
    print("🧩 Renderitzant plantilla YAML sense Jinja2...")
    with open(TEMPLATE_FILE) as f:
        content = f.read()

    def replacer(match):
        var = match.group(1)
        return env_vars.get(var, f"<{var}-NO-TROBAT>")

    rendered = re.sub(r"\$\{(\w+)\}", replacer, content)

    # RENDERED_FILE.parent.mkdir(exist_ok=True)
    with open(RENDERED_FILE, "w") as f:
        f.write(rendered)
    print(f"✅ Fitxer renderitzat a {RENDERED_FILE}")

def stack(extra_args=[]):
    render()
    run(["docker", "stack", "deploy", "-c", str(RENDERED_FILE), env_vars["PROJECT_NAME"], *extra_args])

def stack_down(extra_args=[]):
    run(["docker", "stack", "rm", env_vars["PROJECT_NAME"], *extra_args])

def deploy(extra_args=[]):
    push()
    render()
    run([
        "docker", "stack", "deploy",
        "-c", env_vars["BASE"],
        "-c", env_vars["GENERATED"],
        "--with-registry-auth",
        *env_vars.get("ARGS", "").split(),
        env_vars["STACK"],
        *extra_args
    ])

def clean(extra_args=[]):
    try:
        os.remove(env_vars["GENERATED"])
        print(f"🧹 Fitxer {env_vars['GENERATED']} eliminat.")
    except FileNotFoundError:
        print(f"ℹ️ Fitxer {env_vars['GENERATED']} no trobat.")

actions = {
    "build": build,
    "up": up,
    "down": down,
    "push": push,
    "render": render,
    "stack": stack,
    "stack-down": stack_down,
    "deploy": deploy,
    "clean": clean,
    "help": help
}

def load_default_env(env_vars):
    default_env = {
        "REGISTRY": "127.0.0.1:5000",
        "IMAGE_NAME": "otsun_notebook",
        "TAG": subprocess.getoutput("git rev-parse --short HEAD"),
        "STACK": "otsun-notebook",
        "BASE": "docker-compose.base.yml",
        "OVERRIDE": "docker-compose.override.yml",
        "SWARM": "docker-compose.swarm.yml",
        "GENERATED": "docker-compose.generated.yml",
        "MODE": "",
        "ARGS": "",
        "NOTEBOOKS_DIR": ".",
        "NUM_WORKER_CONTAINERS": "6",
        "NUM_WORKERS_PER_CONTAINER": "1",
    }
    for key, value in default_env.items():
        env_vars.setdefault(key, value)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Gestor de serveis Docker per al projecte."
    )
    parser.add_argument(
        "command",
        choices=actions.keys(),
        help="Comanda a executar"
    )
    parser.add_argument(
        "-e", "--env-file",
        type=str,
        default=".env",
        help="Fitxer d'entorn a carregar (per defecte: .env)"
    )
    args, extra_args = parser.parse_known_args()
    ENV_FILE = BASE_DIR / args.env_file
    env_vars = dotenv_values(ENV_FILE)

    load_default_env(env_vars)
    os.environ.update(env_vars)
    actions[args.command](extra_args)