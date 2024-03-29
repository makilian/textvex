import chromadb
from chromadb.config import Settings
import json
import argparse
import os
import sqlite3
import vobject

contacts = {}

def clean_number(in_phone):
    digits_only = ''.join([char for char in in_phone if char.isdigit()])

    if len(digits_only) and digits_only[0] == '1' and len(digits_only) == 11:
        digits_only = digits_only[1:]
    return digits_only

def get_contact_name(phone_number):
    if phone_number:
        pns = phone_number.split(",")
        for p in pns:
            if not '@' in p:
                p_dig = clean_number(p)
                if p_dig in contacts:
                    name = contacts[p_dig]
                    return name
                else:
                    return 'Person'
            else:
                if p in contacts:
                    name = contacts[p]
                    return name
                else:
                    return 'Person'
    else:
        return 'Person'

def parse_vcards(vcard_file):
    with open(vcard_file, "r") as f:
        vcard_data = f.read()

    vcards = list(vobject.readComponents(vcard_data))

    for vcard in vcards:
        for i, tel in enumerate(vcard.contents.get('tel', [])):
            tele = clean_number(tel.value)
            if hasattr(vcard, "fn"):
                contacts[tele] = vcard.fn.value
            else:
                contacts[tele] = "no fn"
        for email in vcard.contents.get('email', []):
            if hasattr(vcard, "fn"):
                contacts[email.value] = vcard.fn.value
            else:
                contacts[email.value] = "no fn"
            

def initialize_database(collection):
    with open('response.json') as f:
        data = json.load(f)

    chunk_size = 5000
    data_chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    ch_ind = 0

    print("Vectorizing text history, this may take a few minutes.. ")
    print("Each chunk takes around 45 seconds.. go make a coffee?")

    for d in data_chunks:
        print("Vectorizing chunk", ch_ind+1, "of", len(data_chunks))
        collection.add(
            documents=[i['text'] for i in d],
            ids=[str(i+ch_ind*chunk_size) for i in range(0, len(d))]
        )
        ch_ind+=1
        
    print("textvex database initialized!")

def query_database(query, collection, quantity):
    results = collection.query(
        query_texts=[query],
        n_results=quantity
    )

    print("\n\nSearching your text history for:", query, "\n")

    res = results['documents'][0]
    for i in res:
        print(i, "\n")

def extract_texts():
    # Took this from https://github.com/1rgs/MeGPT/blob/main/extract_messages.py

    # Get the user's home directory
    print("Extracting iMessage texts... ")
    home = os.path.expanduser("~")
    output_file = "response.json"

    # Path to the SQLite database
    db_path = f"{home}/Library/Messages/chat.db"

    # Check and update read permission if needed
    if not os.access(db_path, os.R_OK):
        try:
            os.chmod(db_path, 0o644)
        except PermissionError as e:
            print(f"Permission Error: {e}")
            print(
                "Please go to System Preferences > Security & Privacy > Privacy > Full Disk Access and give Terminal full disk access and try again."
            )
            exit(1)

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Run the query
    query = """
    WITH messages_with_prev AS (
        SELECT m.ROWID, m.guid, m.text, m.subject, m.country, m.date, chj.chat_id, m.is_from_me,
               LAG(m.is_from_me) OVER (PARTITION BY chj.chat_id ORDER BY m.date) AS prev_is_from_me,
               h.id as pn, h.uncanonicalized_id
        FROM message AS m
        JOIN chat_message_join AS chj ON m.ROWID = chj.message_id
        LEFT JOIN handle AS h ON m.handle_id = h.ROWID
        WHERE LENGTH(m.text) > 0
    ),
    grouped_messages AS (
        SELECT *,
               SUM(CASE WHEN is_from_me != IFNULL(prev_is_from_me, -1) THEN 1 ELSE 0 END) OVER (PARTITION BY chat_id ORDER BY date) AS grp
        FROM messages_with_prev
    ),
    consecutive_messages AS (
        SELECT chat_id, is_from_me, group_concat(text, '\n') AS joined_text, MIN(date) AS min_date, pn AS speaker
        FROM grouped_messages
        GROUP BY chat_id, is_from_me, grp
    ),
    my_consecutive_messages AS (
        SELECT * FROM consecutive_messages WHERE is_from_me = 1
    ),
    other_consecutive_messages AS (
        SELECT * FROM consecutive_messages WHERE is_from_me = 0
    )
    SELECT other.joined_text AS prev_text, my.joined_text AS my_text, other.speaker AS speaker,
            datetime(other.min_date/1000000000, 'unixepoch', '+31 years') AS other_datetime, datetime(my.min_date/1000000000, 'unixepoch', '+31 years') AS my_datetime
            FROM my_consecutive_messages AS my
    LEFT JOIN other_consecutive_messages AS other ON my.chat_id = other.chat_id AND other.min_date < my.min_date
    WHERE other.min_date = (
        SELECT MAX(min_date) FROM other_consecutive_messages AS ocm
        WHERE ocm.chat_id = my.chat_id AND ocm.min_date < my.min_date
    )
    ORDER BY my.min_date;
    """
    cursor.execute(query)

    # Fetch the results
    results = cursor.fetchall()

    # remove all newlines
    results = [tuple(map(lambda x: x.replace("\n", " ") if isinstance(x, str) else x, row)) for row in results]
    results = [(row[0], row[1], get_contact_name(row[2]), row[3], row[4]) for row in results]

    with open(output_file, "w+") as f:
        json.dump(
            [{"text": f"{row[3]} {row[2]}: {row[0]}\n {row[4]} Me: {row[1]}", "label": 0} for row in results],
            f,
            indent=4,
        )

    print(f"Saved {len(results)} messages to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Initialize or search the database.")
    parser.add_argument("mode", choices=["init", "query"], help="Choose 'init' to populate the database or 'query' to query it.")
    parser.add_argument("-q", "--query", help="The query to search in the database.")

    args = parser.parse_args()

    chroma_client = chromadb.Client(Settings(chroma_db_impl="duckdb+parquet",
                                        persist_directory="./.chroma",
                                        anonymized_telemetry=False
                                    ))

    collection = chroma_client.get_or_create_collection("texts")


    if args.mode == "init":
        vcard_file = "./contacts.vcf"  # Replace with the actual path to your vCard file
        parse_vcards(vcard_file)
        extract_texts()
        initialize_database(collection)
    elif args.mode == "query":
        if args.query:
            query_database(args.query, collection, 20)
        else:
            print("Please provide a query using the -q or --query flag.")

if __name__ == "__main__":
    main()
