
import yarp
import sys
import time
import json
import os.path
import importlib
import inspect
from openai import AzureOpenAI


class LLMchat(yarp.RFModule):

    def configure(self, rf) :
        self.period = 1/30

        self.agent_text_portName = "/agent/text:i"
        self.agent_text_port = yarp.BufferedPortBottle()
        self.agent_text_port.open(self.agent_text_portName)

        self.agent_output_portName = "/agent/text:o"
        self.agent_output_port = yarp.BufferedPortBottle()
        self.agent_output_port.open(self.agent_output_portName)

        # Open RPC client ports
        self.client_action_rpc_port = yarp.RpcClient()
        self.client_action_rpc_port.open("/client_action_rpc")  # Name of the local port

        # if not yarp.Network.connect("/client_action_rpc", "/server_rpc"):
        #     print("Error connecting to /server port")
        #     exit()

        self.client_emotion_rpc_port = yarp.RpcClient()
        self.client_emotion_rpc_port.open("/client_emotion_rpc")  # Name of the local port

        # if not yarp.Network.connect("/client_emotion_rpc", "/server_rpc"):
        #     print("Error connecting to /server port")
        #     exit()
        
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
        
        bottle = self.agent_text_port.read()
        text_input = ""
        if bottle is not None:
           for i in range(bottle.size()):
               message = bottle.get(i).asString()  # Assuming messages are strings
               text_input+=message + " "
        bottle.clear()

        skip_exec = False

        if text_input == "":
            skip_exec = True

        if not skip_exec:
            print("💬 Human: "+ text_input)
            self.messages.append({"role": "user", "content": text_input})
            response = self._query_llm(self.messages)
            self.messages.append(response.choices[0].message)

            if (response.choices[0].message.content is not None):
                print("🤖💭 ergoCub: " + response.choices[0].message.content +'\n')

            bot = self.agent_output_port.prepare()
            bot.clear()
            bot.addString(response.choices[0].message.content)
            self.agent_output_port.write()
    
        return True

    def reset(self): 
        self.messages = [
            {"role": "system", "content": self.character},
        ]
        print(f"📝 Message history reset.")


    def getPeriod(self):
        return self.period
    
        
    def close(self):
        self.agent_text_port.close()
        self.client_action_rpc_port.close()
        self.client_emotion_rpc_port.close()
        self.agent_output_port.close()
        return True
    
    
    def interruptModule(self):
        self.agent_text_port.interrupt()
        self.client_action_rpc_port.interrupt()
        self.client_emotion_rpc_port.interruption()
        self.agent_output_port()
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
