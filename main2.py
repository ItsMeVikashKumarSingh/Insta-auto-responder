import os
import sys
from src.direct import InstagramDirect
import json
import random
import time
import datetime
import requests

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_dir('accounts')
ensure_dir('responded_users')
ensure_dir('locks')

console_width = os.get_terminal_size().columns
print('-' * console_width)

def choose_account():
    config_files = [f for f in os.listdir('accounts') if f.endswith('.json')]

    if not config_files:
        print("There's no config file in 'accounts'.")
        return None

    for i, file in enumerate(config_files):
        print(f'{i + 1}. {file}')

    console_width = os.get_terminal_size().columns
    print('-' * console_width)

    file_num = int(input("Select account: ")) - 1
    config_file = config_files[file_num]
    account_name, _ = os.path.splitext(config_file)

    print(f"Selected account: {account_name}")

    with open(f'accounts/{config_file}', 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def has_responded(account_name, user_id):
    file_name = f'responded_users/{account_name}.json'
    if not os.path.exists(file_name):
        return False
    with open(file_name, 'r', encoding='utf-8') as f:
        responded_users = json.load(f)
    return str(user_id) in responded_users

def mark_as_responded(account_name, user_id, username):
    file_name = f'responded_users/{account_name}.json'
    responded_users = {}
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            responded_users = json.load(f)
    responded_users[str(user_id)] = username
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(responded_users, f)

def get_ai_response(message, brainshop_key, brainshop_bid, user_id):
    """Fetch AI response from Brainshop API using the user's message."""
    url = f"http://api.brainshop.ai/get?bid={brainshop_bid}&key={brainshop_key}&uid={user_id}&msg={message}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('cnt')
        else:
            print(f"Error fetching AI response: {response.status_code}")
            return None
    except Exception as e:
        print(f"Failed to contact Brainshop API: {str(e)}")
        return None

config = choose_account()

if config is None:
    print("Can't load config.")
else:

    while True:
        continue_choice = input("Do you want to continue? (yes/no): ").lower()
        if continue_choice in ["yes", "no"]:
            break
        else:
            print("Please enter 'yes' or 'no'.")

    if continue_choice == "no":
        print("Exiting.")
        sys.exit()

    lock_file = os.path.join('locks', f"{config['account']}.lock")

    if os.path.exists(lock_file):
        print(f"Account {config['account']} is already running. Exiting.")
        sys.exit()
    else:
        open(lock_file, 'a').close()

    session = InstagramDirect(config)
    session.test_proxy()

    message_counter = 0
    while message_counter < config['num_replies']:
        user_ids = session.get_direct_threads()
        all_responded = all(has_responded(config['account'], user_id) for _, user_id, _ in user_ids)
        if all_responded:
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: All users from direct threads have been responded to. Checking spam inbox...")
            user_ids = session.get_direct_threads_spam()  # Check spam inbox if all users from get_direct_threads have been responded to
        if not user_ids:
            wait_time = random.randint(10, 30)  # Adjust the wait time as needed
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: No new threads in inbox or spam inbox. Waiting for {wait_time} seconds before checking for new threads...")
            time.sleep(wait_time)
        for thread_id, user_id, username in user_ids:
            if message_counter >= config['num_replies']:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Reached reply limit ({config['num_replies']}). Stopping message sending.")
                break
            if has_responded(config['account'], user_id):
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Already responded to user {username} ; Skipping.")
                time.sleep(random.randint(10, 60))  # Adjust the wait time as needed
                continue

            # Fetch the last message from the user in the thread
            user_message = session.get_last_message(thread_id)  # Assuming `get_last_message` retrieves the user's message from the thread
            
            # Fetch AI response from Brainshop API using user's message
            message = get_ai_response(user_message, config['brainshop_key'], config['brainshop_bid'], user_id)
            
            # If API fails, fall back to random choice
            if not message:
                message = random.choice(config['messages'])
            
            session.send_message(thread_id, message)
            mark_as_responded(config['account'], user_id, username)
            wait_time = random.randint(60, 90)  # Adjust the wait time as needed
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: [{message_counter+1}/{config['num_replies']}] Responded to user {username} sent message: '{message}' ; waiting {wait_time} seconds before sending message to next user.")
            message_counter += 1
            time.sleep(wait_time)

    if os.path.exists(lock_file):
        os.remove(lock_file)
