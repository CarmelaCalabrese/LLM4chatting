
import yarp
import sys
import time
import json
import os.path
from openai import AzureOpenAI


class LLMchat(yarp.RFModule):

    def configure(self, rf) :

        self.period = 0.1
        self.LLMchat_input_portName = "/LLMchat/text:i"
        self.LLMchat_input_port = yarp.BufferedPortBottle()
        self.LLMchat_input_port.open(self.LLMchat_input_portName)

        self.LLMchat_output_portName = "/LLMchat/text:o"
        self.LLMchat_output_port = yarp.BufferedPortBottle()
        self.LLMchat_output_port.open(self.LLMchat_output_portName)

        self.config_path = rf.check("config", yarp.Value("")).asString()
        if not self.config_path:
            print("Error: config file path is missing")
            return False

        # Load sequences from JSON file
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except Exception as e:
            print(f"Error loading sequences file: {e}")
            return False

        self.azureOpenAI_client = AzureOpenAI(
            azure_endpoint = self.config['endpoint'], 
            api_key=os.getenv("AZURE_API_KEY"),
            api_version=self.config['api_version']
            )
        self.model = self.config['model_name']
        self.temperature = self.config['temperature']
        self.top_p = self.config['top_p']
        self.max_length = self.config['max_length']
        self.character: str = self.config['system_prompt']
        print(self.character)
        self.messages = [
            {"role": "system", "content": self.character},
            ]

        return True
        

    def _query_llm(self, messages):
        response = ""
        response = self.azureOpenAI_client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            top_p = self.top_p,
            max_tokens = self.max_length,
            messages=messages,

        )
        return response

    
    def updateModule(self):
        
        bottle = self.LLMchat_input_port.read()
        text_input = ""
        if bottle is not None:
            for i in range(bottle.size()):
                message = bottle.get(i).asString()  
                text_input+=message

        # Optionally, clear the bottle after reading
        bottle.clear()

        skip_exec = False

        if text_input == "":
            skip_exec = True

        if not skip_exec:
            print("💬 Human: "+ text_input)
            self.messages.append({"role": "user", "content": text_input})

            start_time = time.time()
            response = self._query_llm(self.messages)
            end_time = time.time()
            print(f'Answer generation time: {end_time-start_time}')
            self.status = 'idle'

            self.messages.append(response.choices[0].message)
            if (response.choices[0].message.content is not None):
                print("🤖💭 ergoCub: " + response.choices[0].message.content +'\n')

            bot = self.LLMchat_output_port.prepare()
            bot.clear()
            bot.addString(response.choices[0].message.content)
            self.LLMchat_output_port.write()
    
        return True

    def reset(self):
        self.messages = [
            {"role": "system", "content": self.character},
        ]
        print(f"📝 Message history reset.")
        return True


    def getPeriod(self):
        return self.period
    
        
    def close(self):
        self.LLMchat_input_port.close()
        self.LLMchat_output_port.close()
        return True
    
    
    def interruptModule(self):
        self.LLMchat_input_port.interrupt()
        self.LLMchat_output_port.interrupt()
        return True
    
#########################################333

if __name__ == '__main__':
    
    yarp.Network.init()

    mod = LLMchat()
    rf = yarp.ResourceFinder()
    rf.setVerbose(True)
    rf.configure(sys.argv)
    mod.runModule(rf)
    yarp.Network.fini()



