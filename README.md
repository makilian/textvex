# TextVex

TextVex is a Python script that allows you to search your iMessage history for specific concepts using ChromaDB.

## Installation

1. Make sure you have Python 3.6 or later installed on your system.
2. Install ChromaDB by running `pip install chromadb`.

## Usage

TextVex has two modes: `initialize` and `query`.

### Initialize

To initialize the database with your iMessage history, run:

```
$ python textvex.py initialize
```

This command will first extract your iMessage texts and save them to a file called response.json. Then, it will vectorize your text history and store it in a ChromaDB database.

Note: This command may take a while to complete, especially if you have a large iMessage history.

### Query
To search your iMessage history for a specific concept, run:

```
$ python textvex.py query -q "your query here"
```

Replace your query here with the concept or text you want to search for in your iMessage history.

## Troubleshooting
If you encounter a permission error when running the script, go to System Preferences > Security & Privacy > Privacy > Full Disk Access, and grant Terminal full disk access.

## License
This project is licensed under the MIT License.