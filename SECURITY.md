# Security

This repository contains scripts that send prompt text to a third-party model API of your choice. They read API keys from environment variables only, never from files, never print them, and `--dry-run` sends nothing.

If you find a problem (a path through which a key could leak, a placeholder bypass that lets protected text reach the model, a dependency sneaking in), email support@uniqai.app with the subject "token-diet security". Please do not open a public issue for it until we have replied; we aim to answer within five working days.
