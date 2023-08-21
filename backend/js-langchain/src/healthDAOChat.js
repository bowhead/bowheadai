import { OpenAI } from "langchain/llms/openai";
import { ConversationalRetrievalQAChain } from "langchain/chains";
import { HNSWLib } from "langchain/vectorstores/hnswlib";
import { OpenAIEmbeddings } from "langchain/embeddings/openai";
import promptSync from 'prompt-sync';
import { initializeAgentExecutorWithOptions } from "langchain/agents";
import { VectorDBQAChain } from "langchain/chains";
import { APIChain } from "langchain/chains";
import * as fs from "fs";
const qaprompt = promptSync();

let qaTemplate = `You are a friendly, conversational personal medical assistant. 

Use the following context about medical records to show to the user the information they need, help find exactly what they want. 
You must give information about user data, find relationships between data and give health recommendations, always making it clear that users should consult a specialist.

The context could be in multiple languages. You should always respond in English even if the context is in another language.
It's ok if you don't know the answer. 

Context:
{context} 

Question:
{question}

Helpful Answer:`;

export const queryBQ = async (query, history,userId) => {
  // Initialize the LLM to use to answer the question.
  const model = new OpenAI({ temperature: 0.8, maxTokens: 500 });
  const directory = "src/healthDAOVector/"+userId;

  // Load the vector store from the same directory
  const vectorStore = await HNSWLib.load(directory, new OpenAIEmbeddings());
  
  const vectorChain = VectorDBQAChain.fromLLM(model, vectorStore);

 
  const qaTool = new ChainTool({
    name: "health-documents-qa",
    description:
      "Health Documents QA - useful for when you need to ask questions about your health information.",
    chain: vectorChain,
  });

  const apiChain = APIChain.fromLLMAndAPIDocs(model, OPEN_METEO_DOCS);

  const apiTool = new ChainTool({
    name: "pubmed-api-recommendations",
    description:
      "Pubmed API - useful for obtaining medical articles and using them to give recommendations",
    chain: apiChain,
  });

  const tools = [
    qaTool,
  ];

  const executor = await initializeAgentExecutorWithOptions(tools, model, {
    agentType: "chat-conversational-react-description",
    verbose: true,
  });

  console.log("Loaded agent.");

  const input0 = "hi, i am bob";

  const result0 = await executor.call({ input: input0 });

  console.log(`Got output ${result0.output}`);

  const input1 = "whats my name?";

  const result1 = await executor.call({ input: input1 });

  console.log(`Got output ${result1.output}`);

  const input2 = "whats the weather in pomfret?";

  const result2 = await executor.call({ input: input2 });

  console.log(`Got output ${result2.output}`);


  return "nada";
};