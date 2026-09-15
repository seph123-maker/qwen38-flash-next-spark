[Home](../README.md) · [Setup](SETUP.md) · [Settings](CONFIGURATION.md) · [Troubleshooting](TROUBLESHOOTING.md)

# Use the server

## Confirm it is ready

Run these on the Spark after launching the published container:

```bash
curl --fail http://127.0.0.1:8000/health
curl --fail http://127.0.0.1:8000/v1/models
```

HTTP 200 from `/health` means the API is ready. The models endpoint should list `qwen3.8-flash-next`. Neither check evaluates the quality of its answers.

## Send a first request

```bash
curl --fail http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "qwen3.8-flash-next",
    "messages": [{"role": "user", "content": "What is 17 + 25? Reply with only the number."}],
    "temperature": 0,
    "seed": 42,
    "max_tokens": 32,
    "chat_template_kwargs": {"enable_thinking": false}
  }'
```

Expect the answer `42` in `choices[0].message.content`. This is a small response check, not a benchmark. The example disables thinking so the small output budget is suitable; applications using thinking need to budget for it.

## Connect Hermes or another OpenAI-compatible client

| Client field | Value |
|---|---|
| Provider type | Custom/OpenAI-compatible endpoint |
| Base URL on the Spark | `http://127.0.0.1:8000/v1` |
| Base URL on another computer | `http://SPARK_ADDRESS:8000/v1` |
| Model | `qwen3.8-flash-next` |
| API key | The published server does not require one; if the client insists on a nonempty field, use a placeholder such as `local` |

Use the port chosen at launch if it differs from 8000. Keep the `/v1` suffix. `localhost` on another computer refers to that computer, not the Spark. Hermes configuration commands can differ by release, so these are the endpoint values rather than an assumed Hermes command sequence.

The server enables automatic tool choice and the `qwen3_coder` parser. A client must still send tool definitions and execute requested tools itself. The model server does not gain access to your files or shell merely because these flags are enabled. Compare one harmless tool operation in your client before starting a long agent session.

## Daily operation

```bash
docker logs --tail 80 qwen38-published
docker stop --time 60 qwen38-published
docker start qwen38-published
```

Let active requests finish before stopping. Restarting reloads model weights; persistent compilation caches do not eliminate that step. Use the name passed to `serve.py` if you chose another name.

`serve.py` refuses an existing container name. Restart an existing container with `docker start`; use a new name for a changed launch configuration. On a single Spark, stop the old full-model server before loading another, even if the containers use different ports.

The published Docker port is bound to all interfaces and the API has no authentication. Expose it only on a network where that is intended, or add authenticated access at your deployment boundary. Do not publish credentials in an issue report.
