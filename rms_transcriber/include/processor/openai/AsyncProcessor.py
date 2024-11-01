import asyncio
import openai
from pubsub import pub
from pprint import pprint as pp

from wxasync import WxAsyncApp, AsyncBind #, Start
from colorama import Fore, Style
from ...config import init_config
apc = init_config.apc

class AsyncProcessor:
    def __init__(self, queue):
        self.queue = queue
        #self.client= openai.OpenAI()
        self.conversation_history=[]
    def clear_history(self):
        self.conversation_history=[]
    async def run_stream_response(self, prompt, model):
       
        ch=self.conversation_history
        client= openai.OpenAI()
        #ch=[]
        ch.append({"role": "user", "content": prompt})
        # Create a chat completion request with streaming enabled
        #pp(conversation_history)
        #pp(ch)  
        print('MODEL:', model)
        assert model
        if 1:
            response = client.chat.completions.create(
                model=model,
                messages=ch, 
                stream=True
            )


        # Print each response chunk as it arrives
        out=[]
        inside_stars = False
        inside_backticks = False
        inside_hash = False
        
               
        for chunk in response:
                
            if hasattr(chunk.choices[0].delta, 'content'):
                content = chunk.choices[0].delta.content
               
                new_content = ''
                i = 0
                if not content:
                    continue
                #print(content, end='', flush=True)
                await self.queue.put(content)
                await asyncio.sleep(0)   
                out.append(content)               
                while i < len(content):
                    if content[i:i+2] == '**':
                        if inside_stars:
                            new_content += f"{Style.RESET_ALL}"
                            inside_stars = False
                        else:
                            new_content += f"{Fore.GREEN}{Style.BRIGHT}"
                            inside_stars = True
                        i += 2  # Skip the next character
                    elif content[i:i+3] == '```':
                        if inside_backticks:
                            new_content += f"{Style.RESET_ALL}"
                            inside_backticks = False
                            i += 3 
                        else:
                            new_content += f"{Fore.RED}{Style.BRIGHT}"
                            inside_backticks = True
                            i += 3
                    # Skip the next two characters
                    elif content[i] == '#' and (i == 0 or content[i-1] == '\n'):  # If the line starts with '#'
                        new_content += f"{Fore.BLUE}{Style.BRIGHT}" + content[i]
                        inside_hash = True
                        i += 1
                    elif content[i] == '\n' and inside_hash:  # If the line ends and we're inside a hash line
                        new_content += f"{Style.RESET_ALL}" + content[i]
                        inside_hash = False
                        i += 1
                    else:
                        new_content += content[i]
                        i += 1
                print(new_content, end='', flush=True)
                #print(content, end='', flush=True)
               
                if new_content:
                    out.append(new_content)
            
            if inside_backticks:  # If we're still inside a code block, add the reset code
                out.append(Style.RESET_ALL)
        pub.sendMessage("done_display", response=())
        ch.append({"role": "assistant", "content": ''.join(out)})
            