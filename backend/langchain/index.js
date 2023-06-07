import express from "express";
import multer from "multer";
import { dirname, join, extname } from "path";
import cors from "cors";
import fs from "fs";
import dotenv from 'dotenv';
import bodyParser from "body-parser";
import { fileURLToPath } from "url";
import os from 'os';
import { bqGenerate } from "./src/generateVector.js";
import { queryBQ } from "./src/healthDAOChat.js";
import {GetConfig} from "./src/helpers/leanConfig.js"

dotenv.config()

const __dirname = dirname(fileURLToPath(import.meta.url));
const vectorsDirectory = join(__dirname, "src", "vectors");

const app = express();
app.use(cors({
  origin: GetConfig('cors')
}));

const PORT = 3001;

// Configurar el middleware para procesar los campos no relacionados con archivos primero
app.use(express.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Configurar multer para guardar los archivos en una carpeta específica
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    const uploadPath = join(__dirname, "uploads",req.body.user_id); // Ruta donde se guardarán los archivos
    console.log(uploadPath)
    // Crear la carpeta si no existe
    if (!fs.existsSync(uploadPath)){
      fs.mkdirSync(uploadPath);
  }
    deleteFolderRecursively(uploadPath);
   
    
    cb(null, uploadPath);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + "-" + Math.round(Math.random() * 1e9);
    const fileExtension = extname(file.originalname);
    cb(null, file.originalname.split(".")[0] + "-" + uniqueSuffix + fileExtension);
  },
});

const deleteFolderRecursively = function (directory_path) {
    if (fs.existsSync(directory_path)) {
      

        fs.readdirSync(directory_path).forEach(function (file, index) {
            var currentPath = join(directory_path, file);
            if (fs.lstatSync(currentPath).isDirectory()) {
              deleteFolderRecursively(currentPath);
            } else {
                fs.unlinkSync(currentPath); // delete file
            }
        });
    }
};


// Configurar multer con la opción de almacenamiento
const upload = multer({ storage });

// Ruta para manejar la carga de archivos
app.post("/upload", upload.array("files"), async (req, res) => {
  // Aquí puedes realizar cualquier acción adicional con los archivos cargados
  //console.log(req.body.vectorName)
  //console.log(req.files);
  console.log(req.body.user_id)
  
  const result = await bqGenerate(req.body.user_id);
  res.json({ response: result });
});

  app.post("/send-message", async (req, res) => {
    const message = req.body.message;
    const history = req.body.history;
    const userId = req.body.userId;

    try {
      // Realizar cualquier procesamiento adicional con el mensaje
      const result = await queryBQ(message,history,userId );
  
      // Enviar la respuesta "Hola mundo"
      res.json({ response: result });
    } catch (error) {
      // Manejar errores si ocurre alguno
      console.error("Error al procesar el mensaje:", error);
      res.status(500).json({ error: "Error en el servidor" });
    }
  });

// Manejo de errores
app.use((err, req, res, next) => {
  console.error(err);
  res.status(500).send("Error al cargar el archivo.");
});

// Iniciar el servidor
app.listen(PORT, () => {
  console.log(`Server started on port ${PORT}`);
});
