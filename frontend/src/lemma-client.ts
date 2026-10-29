import { LemmaClient } from 'lemma-sdk'

// Config (podId / apiUrl / authUrl) is injected by the Lemma host at serve time,
// so the same build runs on any pod and nothing pod-specific is baked in.
export const lemmaClient = new LemmaClient()
