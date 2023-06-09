import { HNSWLib } from "@bowhead/langchain/vectorstores/hnswlib";
import { OpenAIEmbeddings } from "@bowhead/langchain/embeddings/openai";
import { DirectoryLoader } from "@bowhead/langchain/document_loaders/fs/directory";
import { TextLoader } from "@bowhead/langchain/document_loaders/fs/text";
import { PDFLoader } from "@bowhead/langchain/document_loaders/fs/pdf";
import { DocxLoader } from "@bowhead/langchain/document_loaders/fs/docx";
import { CSVLoader } from "@bowhead/langchain/document_loaders/fs/csv";
import { dirname, join, extname } from "path";
import { fileURLToPath } from "url";

import fs from 'fs';
const __dirname = dirname(fileURLToPath(import.meta.url));

const createDirectoryIfNotExists = async (directory) => {
  try {
    await fs.promises.mkdir(directory);
    console.log("Directory for vector created");
  } catch (error) {
    if (error.code === 'EEXIST') {
      console.log("vector directory already exists");
    } else {
      console.error("Failed to create directory:", error);
    }
  }
};

export const bqGenerate = async (user_id) => {
  // Initialize the LLM to use to answer the question.

  const loader = new DirectoryLoader("uploads/"+user_id,
  {
    ".txt": (path) => new TextLoader(path),
    ".pdf": (path) => new PDFLoader(path),
    ".docx": (path) => new DocxLoader(path),
    ".csv": (path) => new CSVLoader(path)
  });
  const docs = await loader.load();

  // Create a vector store from the documents.
  const vectorStore = await HNSWLib.fromDocuments(docs, new OpenAIEmbeddings());

  // Crear la carpeta si no existe
  const directory = "src/healthDAOVector/"+user_id;
  await createDirectoryIfNotExists(directory);

  // Save the vector store to a directory
  await vectorStore.save(directory);

  console.log("Vector created");
  return 'vector created successfully';

};