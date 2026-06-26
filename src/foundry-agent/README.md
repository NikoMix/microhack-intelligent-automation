# iauto-foundry-agent

Lab 4 package for migrating a Copilot Studio knowledge agent to a code-first Microsoft Agent Framework RAG agent on the shared `iauto_inference` layer. Retrieval is pluggable behind a `Retriever` protocol: a license-free **offline BM25 `KeywordRetriever`** (zero Azure, no extra dependency) is the free default, and **`AzureSearchRetriever`** is the optional managed upgrade.
