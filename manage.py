#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path
from dotenv import dotenv_values
import re
import argparse

BASE_DIR = Path(__file__).resolve().parent


BASE_TEMPLATE_FILE = BASE_DIR / "docker-compose.base.yml.template"
BASE_RENDERED_FILE = BASE_DIR / "docker-compose.base.yml"
SWARM_TEMPLATE_FILE = BASE_DIR / "docker-compose.swarm.yml.template"
SWARM_RENDERED_FILE = BASE_DIR / "docker-compose.swarm.yml"
OVERRIDE_FILE = BASE_DIR / "docker-compose.override.yml"

        
        # "BASE": "docker-compose.base.yml",
        # "OVERRIDE": "docker-compose.override.yml",
        # "SWARM": "docker-compose.swarm.yml",

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
  clean         - Elimina el fitxer generat
""")

def build(extra_args=[]):
    files = ["-f", str(BASE_RENDERED_FILE), "-f", str(OVERRIDE_FILE)]
    run(["docker", "compose", *files, "build", *extra_args])

def build_swarm(extra_args=[]):
    files = ["-f", str(BASE_RENDERED_FILE), "-f", str(SWARM_RENDERED_FILE)]
    run(["docker", "compose", *files, "build", *extra_args])

def up(extra_args=[]):
    files = ["-f", str(BASE_RENDERED_FILE), "-f", str(OVERRIDE_FILE)]
    run(["docker", "compose", *files, "up", *extra_args])

def down(extra_args=[]):
    files = ["-f", str(BASE_RENDERED_FILE), "-f", str(OVERRIDE_FILE)]
    run(["docker", "compose", *files, "down", *extra_args])

def render(extra_args=[]):
    def replacer(match):
        var = match.group(1)
        return os.environ.get(var, f"<{var}-NO-TROBAT>")

    for (template_file, rendered_file) in [
        (BASE_TEMPLATE_FILE, BASE_RENDERED_FILE),
        (SWARM_TEMPLATE_FILE, SWARM_RENDERED_FILE)
    ]:
        with open(template_file) as f:
            content = f.read()

        rendered = re.sub(r"\$\{(\w+)\}", replacer, content)
        with open(rendered_file, "w") as f:
            f.write(rendered)
        print(f"✅ Fitxer renderitzat a {rendered_file}")


def push(extra_args=[]):
    build_swarm(extra_args=extra_args)
    files = ["-f", str(BASE_RENDERED_FILE), "-f", str(SWARM_RENDERED_FILE)]
    run(["docker", "compose", *files, "push", *extra_args])

def stack(extra_args=[]):
    run(["docker", "stack", "deploy", 
         "-c", str(BASE_RENDERED_FILE), "-c", str(SWARM_RENDERED_FILE), 
         "--with-registry-auth",
         os.environ["STACK_NAME"], *extra_args])

def stack_down(extra_args=[]):
    run(["docker", "stack", "rm", os.environ["STACK_NAME"], *extra_args])

def clean(extra_args=[]):
    for template_file in BASE_DIR.rglob("*.template"):
        target_file = template_file.with_suffix('')  # treu la part .template
        if target_file.exists():
            try:
                target_file.unlink()
                print(f"🗑️ Esborrat: {target_file}")
            except Exception as e:
                print(f"⚠️ No s'ha pogut esborrar {target_file}: {e}")

actions = {
    "build": build,
    "up": up,
    "down": down,
    "push": push,
    "render": render,
    "stack": stack,
    "stack-down": stack_down,
    "clean": clean,
    "help": help
}

def load_default_env(env_vars):
    default_env = {
        "REGISTRY": "127.0.0.1:5000",
        "IMAGE_NAME": "otsun_notebook",
        "TAG": subprocess.getoutput("git rev-parse --short HEAD"),
        "STACK_NAME": "otsun-notebook",
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
    for k, v in env_vars.items():
        os.environ.setdefault(k, v)    
    render()
    actions[args.command](extra_args)