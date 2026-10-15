# Enable AI explanations

I integrated two optional explanation providers in `riskflow/ai.py`: OpenAI's Responses API and a local Ollama service. Both receive the existing scored evidence and return a summary, cited observations, and suggested review steps. Neither provider calculates the risk score or records a decision.

The default Offline template is deterministic and explicitly labeled **no AI**. The included AI tests use mocked provider responses; a successful live response must be verified separately after setup.

## OpenAI setup on Windows

1. Create an API key in the [OpenAI developer platform](https://platform.openai.com/api-keys) and configure API billing/access as required by that account. Keep the key private; do not paste it into GitHub, the browser source, or an issue.
2. Open PowerShell in the extracted RiskFlow folder, which contains `README.md`. Create a local configuration file only if one does not already exist:

   ```powershell
   if (!(Test-Path .env)) { Copy-Item .env.example .env }
   notepad .env
   ```

3. Fill in these two existing lines, save the file, and close Notepad:

   ```dotenv
   OPENAI_API_KEY=YOUR_PRIVATE_API_KEY
   OPENAI_MODEL=YOUR_STRUCTURED_OUTPUTS_COMPATIBLE_MODEL_ID
   ```

   Replace both placeholders. Choose an API model available to the account that supports the Responses API and Structured Outputs. The model ID is an API identifier, not a ChatGPT display name. The existing Python adapter makes the HTTP request directly; an extra OpenAI SDK installation is not required.

4. Generate the synthetic workspace if this is the first run:

   ```powershell
   python -m riskflow demo
   ```

5. Test one explanation:

   ```powershell
   python -m riskflow summary --provider openai --case credit:C0005
   ```

6. For the interface, run `python -m riskflow serve`, open http://127.0.0.1:8000, open a case, select **OpenAI**, and click **Generate summary**. Restart an existing RiskFlow server after changing configuration because already-loaded environment values take precedence.

On Windows, `py -3` can replace `python` if needed. The `.env` file is excluded from Git and the packaged project.

## Verify the live result

A successful command response has `provider: "openai"`, the model identifier, cited `evidence_id` values, and no warning. The interface labels it **AI explanation**. Check the interpretation against the visible case evidence before using it.

If the response instead has `provider: "offline-template"`, the live call or validation failed. A successful command exit alone does not prove a live AI call succeeded. Check API access/billing, the key, model compatibility, the network connection, and server restart. A provider response can also be rejected for unsupported evidence or invented numerical tokens.

The validation checks structure, allowed next steps, references, numerical tokens, and selected disallowed decision language. It cannot establish that every generated sentence is factually correct.

## Local Ollama option

Install Ollama from its official site and start its local service. The adapter expects `http://127.0.0.1:11434`. The default model is `llama3.2`; download that model using `ollama pull llama3.2`, or set `OLLAMA_MODEL` in `.env` to an installed compatible model.

Run:

```powershell
python -m riskflow summary --provider ollama --case credit:C0005
```

Alternatively choose **Local Ollama** in a case's summary menu. Confirm that the returned provider is `ollama`, rather than the fallback, and inspect the generated explanation.

## Data flow

I send only the synthetic case ID, risk type, score, band, evidence, and allowed next steps. Analyst notes, evaluation labels, and credentials are excluded from the fact packet. OpenAI requests use `store: false`; that setting is not a guarantee of zero retention under every service policy. Local summaries are saved under ignored `reports/summaries/` when invoked through the application or CLI.

## References

- [Official OpenAI developer quickstart](https://developers.openai.com/api/docs/quickstart): API keys and first requests.
- [Official OpenAI Structured Outputs guide](https://developers.openai.com/api/docs/guides/structured-outputs): schema-constrained responses and supported model requirements.
