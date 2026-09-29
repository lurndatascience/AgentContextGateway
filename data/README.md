# data

Not committed. The gateway expects this layout, and the Docker build copies the folder into the image:

```
data/
  press_releases/*.txt   one press release per file, named by document id
  records.jsonl          one structured record per release: doc_id, title, summary, entities, key_metrics
  internal_notes.jsonl   team messages: id, channel, author, sent_at, scope, text, optional facts[]
```

Financial facts are parsed from the press releases at ingest and need no file of their own.
