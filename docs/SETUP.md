[Home](../README.md) · [Setup](SETUP.md) · [Settings](CONFIGURATION.md) · [Tests](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Sources](SOURCES.md)

# Set up the tested configuration

Run these commands on the Linux ARM64 Spark, from a clone of this repository. They install a full model server; they are not commands for the Windows machine used to browse this guide.

```bash
git clone https://github.com/seph123-maker/qwen38-flash-next-spark.git
cd qwen38-flash-next-spark
```

## Build and launch

Requires an ARM64 GB10 system, Docker with NVIDIA GPU support, Python 3, and the pinned checkpoint prepared with the included hybrid converter. Weights are not distributed in this package. This build recipe matches the production sources; a clean build of this publication bundle has not been rerun. Build output hashes can differ even with pinned inputs.

From this directory:

```bash
docker build -f upstream/Dockerfile.block-a -t qwen38-published:20260915 upstream
```

Use an isolated Hugging Face cache when preparing the pinned revision. With the Hugging Face CLI installed and model access accepted where required:

```bash
export HF_CACHE="$PWD/model-cache"
export MODEL=drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47
hf download "$MODEL" --revision a393318fb56d9aedc56d91b6f4962d9af26d2fe7 --cache-dir "$HF_CACHE/hub"
( cd upstream && IMAGE=qwen38-published:20260915 bash scripts/prepare-hybrid.sh )
python3 serve.py --hf-cache "$HF_CACHE" --compile-cache "$PWD/compile-cache"
```

The preparation script selects the downloaded snapshot and creates its `-fp8hybrid` sibling. The launcher pins that exact sibling. If using a populated cache containing other revisions, explicitly verify which snapshot the converter selected. The converter uses source-relative tools, so run it from `upstream` as shown. It is a one-time weight conversion, not part of server startup.

The launcher refuses to replace an existing container. Allow the current model server to finish requests and stop it before loading this full model on the same Spark. First weight loading on this system took roughly 8–13 minutes. The API binds all interfaces without authentication, matching the measured configuration; choose network exposure appropriate to your deployment.

```bash
docker logs -f qwen38-published
curl --fail http://127.0.0.1:8000/health
```

Hermes OpenAI base URL: `http://SPARK_ADDRESS:8000/v1`; model `qwen3.8-flash-next`. An HTTP health response confirms readiness, not model quality. `python3 serve.py --hf-cache /path/to/cache --dry-run` prints the complete launch command without starting anything.

## Reuse an existing prepared model

If you already have this exact revision and its prepared `-fp8hybrid` directory, skip downloading and conversion. Pass the existing Hugging Face cache root to `serve.py`. The launcher checks for the pinned path; it does not select whichever model was downloaded last.

## Check the package before using it

From the repository root on Linux:

```bash
sha256sum --check SHA256SUMS
```

These hashes detect changes relative to this checkout. They are not a signature or independent proof of who published the files. They do not cover downloaded weights or externally fetched build dependencies.
