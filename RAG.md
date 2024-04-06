# Retrieval Augmented Generation using Engineering Design Knowledge
In this document, I describe how Large-Language Models (LLMs) could be instructed to generate factual responses to support various applications in the engineering design process. 
I put forward three scenarious as follows.

 - Scenario 1: Directly asking LLM about a component or an issue.
 - Scenario 2: Provide a text document as a reference and asking LLM about a component or an issue.
 - Scenario 3: Providing design knowledge in the form of facts (entity :: relationship :: entity) as a reference.

The tenet of my research is that design knowledge, when explicated as facts, could be more beneficial for interacting with LLMs and generating more meaningful responses for engineering design applications.
The underlying method for explicating facts is described in the following paper.

*Siddharth, L., Luo, J., 2024. Engineering Design Knowledge Graphs from Patented Artefact Descriptions for Retrieval-Augmented Generation in the Design Process. arXiv (cs.CL) https://arxiv.org/abs/2307.06985.*

First, let us understand how LLMs are used for generating text according to our needs. The following function could be used for interacting with GPT through API.
```
from openai import OpenAI
#For API key, visit 'https://platform.openai.com/api-keys'
client = OpenAI(api_key="Your API Key")

#For other latest models, visit 'https://platform.openai.com/docs/models/overview'
def gpt(temperoryChat, textGenerationModel="gpt-3.5-turbo-1106"):
    completion = client.chat.completions.create(
      model=textGenerationModel,
      messages=temperoryChat)
    
    return str(completion.choices[0].message.content)
```

The general syntax is to provide system instructions and user input/query in the following format to generate a response.
```
chat = [
    {"role": "system", "content": "Necessary instructions, rules, and conditions to be given here."},
    {"role": "user", "content": "The main task or query to be given here"}
]
output = gpt(chat)
print(output)
```
As the code required to interact with GPT is clear, let us understand how GPT could be used and instructed with specific context.
Here, I am focussing on the domain of fan systems and try to understand a key component and a notable issue through GPT.

Belt drive is a key component in fan systems. Let us ask GPT to describe it as follows.

```
#The instructions could be altered in any way preferable.
chat = [
    {"role": "system", "content": "The output should be a single paragraph within 100 words."},
    {"role": "user", "content": "Provide a technical description of belt drives in fan systems."}
]
print(gpt(chat), "\n\n")
```
The above code results in the following output.
>In fan systems, belt drives are used to transfer power from the motor to the fan shaft. A belt drive typically consists of a belt, pulleys, and a tensioning system. The motor's rotational energy is transferred to the fan shaft through the friction between the belt and the pulleys. The pulleys are usually connected by the belt and are of different sizes to create a speed differential between the motor and the fan. Tensioning systems are used to adjust the tension of the belt, ensuring proper power transmission. Belt drives are chosen for fan systems due to their efficiency, flexibility in speed adjustments, and cost-effectiveness. 

The above output appears quite common-sensical and devoid of references 
In the [work](https://arxiv.org/abs/2307.06985) referred earlier, I retrieved 4,870 patents related to fan systems and applied the proposed method in the paper to extract facts from the sentences in these.
The extraction lead to populating over 2.9 million facts that consitute a knowledge base of fan systems.

In retrieval augmented generation, context for GPT could either be portion of these patents or the facts extracted these.

