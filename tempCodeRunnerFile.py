import time
import sys
import re
import asyncio
import telethon
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import SessionPasswordNeededError

def is_valid_string(string):
    # Verifica se la stringa contiene almeno un numero
    if not any(char.isdigit() for char in string):
        return False
    return True

class TelegramForwarder:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('session_' + phone_number, api_id, api_hash)

    async def list_chats(self):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            try:
                await self.client.sign_in(self.phone_number, input('Enter the code: '))
            except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
                password = input('Enter your two-step verification password: ')
                await self.client.sign_in(password=password)

        # Get a list of all the dialogs (chats)
        dialogs = await self.client.get_dialogs()
        with open(f"chats_of_{self.phone_number}.txt", "w", encoding='utf-8') as chats_file:
        # Print information about each chat
            for dialog in dialogs:
                print(f"Chat ID: {dialog.id}, Title: {dialog.title}".encode('utf-8', errors='replace').decode('utf-8'))
                chats_file.write(f"Chat ID: {dialog.id}, Title: {dialog.title} \n")

        print("List of groups printed successfully!")


    async def forward_messages_to_channel(self, source_chat_id, destination_identity):
        await self.client.connect()

        # Ensure you're authorized
        if not await self.client.is_user_authorized():
            await self.client.send_code_request(self.phone_number)
            try:
                await self.client.sign_in(self.phone_number, input('Enter the code: '))
            except telethon.errors.rpcerrorlist.SessionPasswordNeededError:
                password = input('Enter your two-step verification password: ')
                await self.client.sign_in(password=password)

        try:
            # Ottieni l'entità del bot tramite il nome utente
            destination_entity = await self.client.get_entity(destination_identity)
        except ValueError as e:
            print(f"Errore durante il recupero dell'entità di destinazione: {e}")
            return

        print(f"Entità di destinazione: {destination_entity}")  # Stampa l'entità di destinazione

        last_message_id = (await self.client.get_messages(source_chat_id, limit=1))[0].id

        while True:
            print("Checking for messages and forwarding them...")
            # Get new messages since the last checked message
            messages = await self.client.get_messages(source_chat_id, min_id=last_message_id, limit=None)

            for message in reversed(messages):
                string_sent = False  # Flag per tenere traccia se una stringa è stata inviata
                #strings = re.findall(r'[a-zA-Z0-9]{44}', message.text)
                strings = []
                obfuscated_strings = []
                sus_strings = []

                try:
                    strings = re.findall(r'[a-zA-Z0-9]{43,44}', message.text)
                except TypeError:
                    print(f"Il messaggio non è una stringa: {message}")
                    continue  # Passa al messaggio successivo

                # Dividi il testo del messaggio in parole
                words = re.split(r'\s+', message.text)

                for word in words:
                    # Cerca la stringa di 44 caratteri in ogni parola
                    matchobf = re.search(r'(?:https?://\S*?/)?([a-zA-Z0-9]+(?:\W*?[a-zA-Z0-9]+)*)', word)
                    matchsplit = re.search(r'(?:https?://\S*?/)?([a-zA-Z0-9]{10,37})', word)
                    if matchobf:
                        obfuscated_string = matchobf.group(1)
                        cleaned_string = re.sub(r'[^\w]', '', obfuscated_string)
                        if len(cleaned_string) == 44 or len(cleaned_string) == 43:
                            obfuscated_strings.append(cleaned_string)
                        elif 6 <= len(cleaned_string) <= 37 and is_valid_string(cleaned_string):
                            sus_strings.append(cleaned_string )  
                    elif matchsplit:
                        if is_valid_string(matchsplit.group(1)):
                            sus_strings.append(matchsplit.group(1))

                if strings:
                    for string in strings:
                        # Forward the 44-character string to the destination channel
                        #await self.client.send_message(destination_channel_id, string)
                        await self.client.send_message(destination_entity, string)
                        print('s')
                        print(f"44-character string forwarded: {string}")
                        string_sent = True
                        break

                if not string_sent and obfuscated_strings:
                    for obfuscated_string in obfuscated_strings:
                        cleaned_string = re.sub(r'[^\w]', '', obfuscated_string)
                        if len(cleaned_string) == 44 or len(cleaned_string) == 43:
                            #await self.client.send_message(destination_channel_id, cleaned_string)
                            await self.client.send_message(destination_entity, obfuscated_string)
                            print('o')
                            print(f"44-character string forwarded: {cleaned_string}")
                            string_sent = True
                            break

                if not string_sent and sus_strings:
                    for i in range(len(sus_strings) - 1):
                        part1 = sus_strings[i]
                        part2_length1 = 44 - len(part1)
                        part2_length2 = 43 - len(part1)
                        for j in range(i + 1, len(sus_strings)):
                            part2 = sus_strings[j]
                            if len(part2) == part2_length1 or len(part2) == part2_length2:
                                if part1.endswith("pump"):
                                    placeholder = part2
                                    part2 = part1
                                    part1 = placeholder
                                full_string = part1 + part2
                                if is_valid_string(full_string):
                                    #await self.client.send_message(destination_channel_id, full_string)
                                    await self.client.send_message(destination_entity, full_string)
                                    print('sp')
                                    print(f"character string forwarded: {full_string}")
                                    string_sent = True
                                    break
                            if string_sent:
                                break  # Se una stringa è stata inviata, interrompi il ciclo interno
                
                last_message_id = max(last_message_id, message.id)

                if string_sent:
                    break  # Se una stringa è stata inviata, interrompi il ciclo e passa al messaggio successivo

            # Add a delay before checking for new messages again
            await asyncio.sleep(1)  # Adjust the delay time as needed


# Function to read credentials from file
def read_credentials():

    try:
        with open("credentials.txt", "r") as file:
            lines = file.readlines()
            api_id = lines[0].strip()
            api_hash = lines[1].strip()
            phone_number = lines[2].strip()
            return api_id, api_hash, phone_number
    except FileNotFoundError:
        print("Credentials file not found.")
        return None, None, None

# Function to write credentials to file
def write_credentials(api_id, api_hash, phone_number):
    with open("credentials.txt", "w") as file:
        file.write(api_id + "\n")
        file.write(api_hash + "\n")
        file.write(phone_number + "\n")

async def main():
    # Attempt to read credentials from file
    api_id, api_hash, phone_number = read_credentials()

    # If credentials not found in file, prompt the user to input them
    if api_id is None or api_hash is None or phone_number is None:
        api_id = input("Enter your API ID: ")
        api_hash = input("Enter your API Hash: ")
        phone_number = input("Enter your phone number: ")
        # Write credentials to file for future use
        write_credentials(api_id, api_hash, phone_number)

    forwarder = TelegramForwarder(api_id, api_hash, phone_number)
    
    print("Choose an option:")
    print("1. List Chats")
    print("2. Forward Messages")
    
    choice = input("Enter your choice: ")
    
    if choice == "1":
        await forwarder.list_chats()
    elif choice == "2":
        source_chat_id = int(input("Enter the source chat ID: "))

        print("Choose the bot type:")
        print("1. Trojan")
        print("2. PepeBoost")
        bot_type = int(input("Enter your choice: "))

        if bot_type == 2:
            bot_number = str(input("Enter the bot[01/15]: "))

        if bot_type == 1:
            destination_entity = '@odysseus_trojanbot'
        elif bot_type == 2:
            destination_entity = '@pepeboost_sol' + bot_number + '_bot'
        
        await forwarder.forward_messages_to_channel(source_chat_id, destination_entity)
        
    else:
        print("Invalid choice")

# Start the event loop and run the main function
if __name__ == "__main__":
    asyncio.run(main())
