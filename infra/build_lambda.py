"""Build the Lambda package folder (infra/build/lambda) with Linux wheels.

Usage: python infra/build_lambda.py
Terraform then zips infra/build/lambda into the deployment package.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "infra" / "build" / "lambda"
# boto3 is already in the Lambda Python runtime, so leave it out to keep the package small.
SKIP = ("boto3",)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    reqs = [line.strip() for line in (ROOT / "requirements-api.txt").read_text().splitlines()
            if line.strip() and not line.startswith(SKIP)]
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--target", str(OUT),
                    "--platform", "manylinux2014_x86_64", "--implementation", "cp",
                    "--python-version", "3.12", "--only-binary=:all:", *reqs], check=True)
    shutil.copytree(ROOT / "clouddesk", OUT / "clouddesk", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", OUT / "data")
    size = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1e6
    print(f"Lambda package ready: {OUT} ({size:.1f} MB unzipped)")


if __name__ == "__main__":
    main()
