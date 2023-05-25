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

export const bqGenerate = async () => {
  // Initialize the LLM to use to answer the question.
  // const text = fs.readFileSync("src/betterQuestDocs/lore_and_info_pros.txt", "utf8");
  // const textSplitter = new RecursiveCharacterTextSplitter({ chunkSize: 1000 });
  // const docs = await textSplitter.createDocuments([text]);

  /*const imgPdfsFolder = 'src/healthDAODocs/unstructure/files/';
  const imgFolder = 'src/healthDAODocs/unstructure/images/';
  fs.readdir(imgFolder, (err, files) => {
    files.forEach(file => {
      console.log(file)
      extractText(file);
    
    });
  });*/

  const loader = new DirectoryLoader("uploads/",
  {
    ".txt": (path) => new TextLoader(path),
    ".pdf": (path) => new PDFLoader(path),
    ".docx": (path) => new DocxLoader(path),
    ".csv": (path) => new CSVLoader(path)
  });
  const docs = await loader.load();

  // Create a vector store from the documents.
  const vectorStore = await HNSWLib.fromDocuments(docs, new OpenAIEmbeddings());

  // Save the vector store to a directory
  const directory = "src/healthDAOVector/";
  await vectorStore.save(directory);

  console.log("Vector created");
  return 'vector created successfully';

};