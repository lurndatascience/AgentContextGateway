# Best agent-user interaction

The exchange that decided the retrieval design. It changed the schema (a late-chunking vector column was added and then removed), the architecture (one vendor, no hosted model, no droplet resize), the workflow (a per-request channel selector so one deployment can be ablated), and a feature (the yes/no judge became a scoring reranker). Hostnames and credentials are redacted; assistant turns are condensed.

---

**User:** did we use late chunking and contextual retrievals inside it?

**Assistant:** No, neither. Chunks are embedded as title plus content, and cited chunks get their structured record attached at resolve time, which is a light version of contextual retrieval. Contextual retrieval is cheap to add from your earlier project's pattern. Late chunking needs a model that exposes token-level embeddings, which the OpenAI API does not offer, so it would mean hosting a model. Recommendation: add contextual retrieval behind a flag and measure it; skip late chunking.

**User:** Yes build the contextual retrieval step and measure it. Also use late chunking

**Assistant:** Building both. Flagging one decision: the droplet has 458 MB of RAM, too small to host a model, so late chunking would go through a third-party embeddings API that supports it natively.

**User:** did we use ranker inside this?

**Assistant:** No reranker today: rank fusion, an IDF-weighted coverage gate, and a yes/no judge that does not reorder. The same third-party API offers a reranker; I will add it as an optional step and measure it in the same ablation.

*(Contextual notes, late-chunking vectors in a new column, the reranker, and per-request channel selection were built.)*

**User:** I don't want to use Jina... can we use something else?

**Assistant:** Two options. One: a different vendor with contextualized chunk embeddings and a reranker on one key. Two: OpenAI only, turning the judge into a 0 to 10 scorer so it reranks, and dropping late chunking because no OpenAI model exposes token vectors. Self-hosting is out at 458 MB.

**User:** 2

*(The third-party module and the late-chunking column were removed. The judge became a scoring reranker with a cutoff. The ablation ran on one deployment.)*

**Assistant:** Ablation: lexical only 80% hit rate; baseline 90%; baseline plus reranker 90% with MRR 0.81 and 50% refusals; contextual alone 85%; contextual plus reranker 90% with MRR 0.85, 55% refusals, and the smallest packages. Contextual notes on their own slightly hurt on this corpus. Deploying contextual plus reranker as the default.

**User:** *(pastes an analysis from elsewhere arguing self-hosted late chunking fits a 4 GB droplet)*

**Assistant:** That analysis assumed 4 GB from the disk size. I measured 458 MB. It also assumes the old stack's dependencies and a 3,072-dimension schema; this gateway has neither. The decision is a hosting one: resize to 4 GB and it is feasible, for a modest gain given the reranker is what moved the numbers.

**User:** Keep OpenAI-only, no resize...

---

## Why this one

The human steered at every fork: asked for both techniques, rejected a vendor, chose the simpler option, then held the line against an outside analysis with a wrong premise. The assistant's job was to make each fork concrete: what each option costs, what it requires, and afterwards what the measurement said. The final design is smaller than the one first requested and measurably better than the baseline, and the ablation table in the README is the evidence.
