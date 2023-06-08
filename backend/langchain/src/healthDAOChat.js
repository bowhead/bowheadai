import { OpenAI } from "@bowhead/langchain/llms/openai";
import { ConversationalRetrievalQAChain } from "@bowhead/langchain/chains";
import { HNSWLib } from "@bowhead/langchain/vectorstores/hnswlib";
import { OpenAIEmbeddings } from "@bowhead/langchain/embeddings/openai";
import promptSync from 'prompt-sync';

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

  // Create a chain that uses the OpenAI LLM and HNSWLib vector store.
  const chain = ConversationalRetrievalQAChain.fromLLM(model, vectorStore.asRetriever(), {
    qaTemplate: qaTemplate,
    returnSourceDocuments: true,
  });
 
  const followUpRes = await chain.call({
    question: query,
    chat_history: history,
  });

  return followUpRes.text;
};