import requests
import json
import uuid
import time
import random
import datetime

class InstagramDirect:
    def __init__(self, account_data):
        self.account_data = account_data
        self.headers = {
            'user-agent': 'Instagram 329.0.0.0.58 Android (25/7.1.2; 320dpi; 900x1600; samsung; SM-G965N; star2lte; samsungexynos9810; en_US; 541635897)',
            'authorization': self.account_data['data']['IG-Set-Authorization'],
        }
        self.data = {
            'device_id': self.account_data['data']['device_id'],
            '_uuid': self.account_data['data']['uuid'],
        }
        self.proxy = self.account_data['data']['proxy']

    def get_direct_threads(self):
        """Fetch direct threads from Instagram."""
        params = {
            'visual_message_return_type': 'unseen',
            'persistentBadging': 'true',
            'limit': '20',
            'is_prefetching': 'false',
            'selected_filter': 'unread',
        }

        # Set up proxies if applicable
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy != "no_proxy" else None
        
        try:
            # Send GET request to the Instagram API
            response = requests.get('https://i.instagram.com/api/v1/direct_v2/inbox/', 
                                    params=params, headers=self.headers, proxies=proxies)
            
            # Introduce a delay to mimic human interaction
            time.sleep(random.randint(3, 10))

            # Check for successful response
            if response.status_code != 200:
                raise Exception(f'Failed to get direct threads: {response.text}')

            # Parse the response JSON
            data = response.json()

            # Check if there are unread threads
            if not data['inbox']['threads']:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Could not find any unread threads.")
                return []

            # Extract user IDs and thread IDs from the threads
            user_ids = [(thread['thread_id'], thread['users'][0]['pk_id'], thread['users'][0]['username']) 
                        for thread in data['inbox']['threads']]

            return user_ids[:self.account_data['num_replies']]
        
        except Exception as e:
            # Enhanced error handling
            print(f"An error occurred while fetching direct threads: {e}")
            if "challenge_required" in str(e):
                print("It seems like you need to verify your account. Please follow the provided link.")
                # Optionally, you could add code here to prompt the user to visit the challenge URL
            return []  # Return an empty list if there's an error

    def get_direct_threads_spam(self):
        """Fetch direct threads from the spam inbox on Instagram."""
        params = {
            'visual_message_return_type': 'unseen',
            'persistentBadging': 'true',
            'limit': '20',
            'is_prefetching': 'false',
        }

        # Set up proxies if applicable
        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy != "no_proxy" else None
        
        try:
            # Send GET request to the Instagram API for spam inbox
            response = requests.get('https://i.instagram.com/api/v1/direct_v2/pending_inbox/', 
                                    params=params, headers=self.headers, proxies=proxies)
            
            # Introduce a delay to mimic human interaction
            time.sleep(random.randint(3, 10))

            # Check for successful response
            if response.status_code != 200:
                raise Exception(f'Failed to get direct threads spam: {response.text}')

            # Parse the response JSON
            data = response.json()

            # Check if there are unread threads in the spam inbox
            if not data['inbox']['threads']:
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Could not find any unread threads in the spam inbox.")
                return []

            # Extract user IDs and thread IDs from the threads
            user_ids = [(thread['thread_id'], thread['users'][0]['pk_id'], thread['users'][0]['username']) 
                        for thread in data['inbox']['threads']]

            return user_ids[:self.account_data['num_replies']]
        
        except Exception as e:
            # Enhanced error handling
            print(f"An error occurred while fetching direct threads from spam inbox: {e}")
            if "challenge_required" in str(e):
                print("It seems like you need to verify your account. Please follow the provided link.")
                # Optionally, you could add code here to prompt the user to visit the challenge URL
            return []  # Return an empty list if there's an error

    def send_message(self, thread_id, message):
        client_context = str(uuid.uuid4()).replace('-', '')
        data = self.data.copy()
        data.update({
            'action': 'send_item',
            'is_x_transport_forward': 'false',
            'is_shh_mode': '0',
            'send_silently': 'false',
            'thread_ids': f'[{thread_id}]',
            'send_attribution': 'direct_thread',
            'client_context': client_context,
            'text': message,
            'mutation_token': client_context,
            'btt_dual_send': 'false',
            "nav_chain": (
                "1qT:feed_timeline:1,1qT:feed_timeline:2,1qT:feed_timeline:3,"
                "7Az:direct_inbox:4,7Az:direct_inbox:5,5rG:direct_thread:7"
            ),
            'is_ae_dual_send': 'false',
            'offline_threading_id': client_context,
        })

        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy != "no_proxy" else None
        response = requests.post('https://i.instagram.com/api/v1/direct_v2/threads/broadcast/text/', headers=self.headers, data=data, proxies=proxies)
        time.sleep(random.randint(3, 10))
        if response.status_code != 200:
            raise Exception(f'Failed to send message: {response.text}')

    def get_last_message(self, thread_id):
        """Fetch the last message sent by the user in a thread."""
        params = {
            'visual_message_return_type': 'unseen',
            'limit': '10',
        }

        proxies = {"http": self.proxy, "https": self.proxy} if self.proxy != "no_proxy" else None
        response = requests.get(f'https://i.instagram.com/api/v1/direct_v2/threads/{thread_id}/', params=params, headers=self.headers, proxies=proxies)
        time.sleep(random.randint(3, 10))
        if response.status_code != 200:
            raise Exception(f'Failed to get last message: {response.text}')

        data = json.loads(response.text)

        # Debugging Step: Print available keys in account_data['data']
        print(f"Available keys in account_data['data']: {self.account_data['data'].keys()}")

        if not data['thread']['items']:
            return None

        # Use the correct key for the bot's user ID, which is 'pk_id' based on the available keys
        bot_user_id = self.account_data['data'].get('pk_id', None)

        if not bot_user_id:
            raise KeyError("'pk_id' or the user ID key is missing in account_data['data']")

        # Get last message not sent by the bot
        last_message = next((item for item in data['thread']['items'] if item['user_id'] != bot_user_id), None)
        
        if last_message:
            return last_message['text'] if 'text' in last_message else None
        else:
            return None
    
    
    def reformat_response(response_text):
        """Reformat the response to remove unwanted tags like <tips> and content inside."""
        import re
        # Regular expression to match tags like <tips>...< /tips>
        return re.sub(r"<.*?>.*?</.*?>", "", response_text).strip()

    def get_ai_response(message, brainshop_key, brainshop_bid, user_id):
        """Fetch AI response from Brainshop API using the user's message."""

        # Build the request URL with appropriate parameters
        url = f"http://api.brainshop.ai/get?bid={brainshop_bid}&key={brainshop_key}&uid={user_id}&msg={message}"

        try:
            # Send a GET request to Brainshop API
            response = requests.get(url)

            # Log the response status code and raw content for debugging purposes
            print(f"Brainshop API response status code: {response.status_code}")
            print(f"Brainshop API raw response: {response.text}")  # This prints the raw text response

            # Check if the response is successful (status code 200)
            if response.status_code != 200:
                print(f"Non-200 response received: {response.status_code} - {response.text}")
                raise Exception(f"Error fetching AI response: {response.status_code}")

            # Check if the response content is empty
            if not response.text:
                raise Exception("Empty response received from Brainshop API.")

            # Parse the response as JSON
            data = response.json()  # This converts the raw response to a Python dictionary

            # Log parsed data for debugging
            print(f"Parsed API response: {data}")

            # Get the 'cnt' field from the API response, which contains the AI's reply
            ai_response = data.get('cnt', None)

            # Reformat the response to remove unwanted tags if the response is not None
            print(f"Original AI response: {ai_response}")  # Log the original text

            # Reformat the response to remove unwanted tags if the response is not None
            if ai_response:
                reformatted_response = reformat_response(ai_response)
                return reformatted_response

            return None  # Return None if there is no content

        except requests.exceptions.RequestException as e:
            # Catch any request-related errors and log them
            print(f"Request failed: {e}")
            return None  # Return None on request failure

        except ValueError as ve:
            # Handle JSON parsing errors
            print(f"Failed to parse the API response as JSON: {ve}")
            return None  # Return None on JSON parsing failure

        except Exception as e:
            # Catch any other unexpected errors and log them
            print(f"An error occurred: {e}")
            return None  # Return None on any other error

    def test_proxy(self):
        if self.proxy == "no_proxy":
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: No proxy is being used.")
            return

        proxies = {"http": self.proxy, "https": self.proxy}
        response = requests.get('https://api.ipify.org?format=json', proxies=proxies)
        proxy_ip = self.proxy.split('@')[1].split(':')[0]
        if response.json()['ip'] != proxy_ip:
            print(f"Expected Proxy IP: {proxy_ip}")
            print(f"Actual Proxy IP: {response.json()['ip']}")
            raise Exception(f'Proxy IP does not match: {response.text}')
        else:
            print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Proxy IP matches.")
