# Preflight dell'ambiente Kaggle

**Data:** 5 settembre 2026

**Stato:** completato

**Ambito:** collaudo tecnico dell'acceleratore; non è l'esperimento scientifico E00

## Obiettivo

Verificare con il minimo consumo possibile che l'account di Matteo possa avviare una sessione GPU Kaggle e che PyTorch riconosca realmente l'acceleratore. Non sono stati collegati dataset, scaricati checkpoint, installati software Vesuvius o prodotti output di ink detection.

## Artefatto esterno

- Notebook privato: [papyruslab-e00-preflight](https://www.kaggle.com/code/matteopontesilli/papyruslab-e00-preflight/edit)
- Stato osservato: bozza salvata, visibilità **Private**, nessun collaboratore aggiunto.
- Versione Kaggle persistente: non creata; il notebook resta una bozza.

## Prova eseguita

Una singola cella ha registrato versione di Python, piattaforma, PyTorch, runtime CUDA, numero di GPU, modello e memoria video dichiarata dal framework. La cella è terminata in 4,634 secondi.

Risultato osservato:

```json
{
  "python": "3.12.13",
  "platform": "Linux-6.12.90+-x86_64-with-glibc2.35",
  "torch": "2.10.0+cu128",
  "cuda_available": true,
  "cuda_runtime": "12.8",
  "gpu_count": 2,
  "gpus": [
    {
      "index": 0,
      "name": "Tesla T4",
      "vram_gib": 14.56
    },
    {
      "index": 1,
      "name": "Tesla T4",
      "vram_gib": 14.56
    }
  ]
}
```

Durante il controllo la pagina di sessione riportava circa 805 MiB di RAM usata, circa 346,6 MiB di disco usato e circa 3 MiB su ciascuna GPU. Questi valori descrivono soltanto il processo minimo e non stimano le risorse necessarie alla pipeline.

## Chiusura e limiti

La sessione è stata arrestata manualmente. L'interfaccia ha successivamente mostrato `Draft Session off (run a cell to start)` e `Session stopped.` Il contatore mostrava 30 ore GPU rimanenti prima dell'avvio; non è stato ricontrollato dopo la prova e non viene quindi dichiarato come saldo finale.

Il preflight dimostra soltanto che in questa sessione PyTorch ha potuto usare due Tesla T4. Non dimostra che:

- la stessa configurazione hardware verrà assegnata in futuro;
- villa, vesuvius o i checkpoint `ink_9um` siano installabili e compatibili;
- un surface volume venga interpretato con assi, scala e orientamento corretti;
- l'inferenza produca una predizione valida o lettere leggibili.

G1 resta quindi aperto: verrà superato soltanto dopo il controllo noto E00, eseguito da un piano congelato e con gli output verificati.
