# textvex

textvex is a Python script that allows you to search your iMessage history for specific concepts using vector embeddings via Chroma (all locally).

## Installation

1. Make sure you have Python 3.6 or later installed on your system.
2. Install Chroma by running `pip install chromadb`.

## Usage

textvex has two modes: `init` and `query`.

### Init

To initialize the database with your iMessage history, run:

```
$ python textvex.py init
```

This command will first extract your iMessage texts and save them to a file called response.json. Then, it will vectorize your text history and store it in a Chroma database. This is all local, no text data leaves your computer!

Note: This command may take a while to complete (45 seconds per 5k of texts), especially if you have a large iMessage history.

### Query
Once initialized, you can search your iMessage history for a specific concept, run:

```
$ python textvex.py query -q "your query here"
```

Some fun examples I've tried: "profuse apology", "song recommendations", "song links", "dinner spots", "flirty", "angry", "negotiation", etc..

Replace your query here with the concept or text you want to search for in your iMessage history.

## Troubleshooting
If you encounter a permission error when running the script, go to System Preferences > Security & Privacy > Privacy > Full Disk Access, and grant Terminal full disk access.

## License
This project is licensed under the MIT License.