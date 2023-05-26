import { Box, Heading, Text, Image, Progress } from "@chakra-ui/react";
import { useState, useRef, useEffect } from "react";
import io from "socket.io-client";

function FileUploader({ onFilesUploaded,deleteOldFiles,  ...props }) {
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    if (files.length > 0) {
      createVector();
      setUploading(true);
      setProgress(10)

    }
  }, [files]);

  function handleDragOver(event) {
    event.preventDefault();
  }

  function handleDragLeave(event) {
    event.preventDefault();
  }

  function handleDrop(event) {
    event.preventDefault();
    const fileList = Array.from(event.dataTransfer.files);
    setFiles(fileList);
  }

  function handleFileInputChange(event) {
    const fileList = Array.from(event.target.files);
    setFiles(fileList);
  }

  useEffect(() => {
    const socket = io("http://localhost:5000/upload");
    socket.on("progress", ({ progress }) => {
      setProgress(progress);
      console.log(progress)
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  

  async function createVector() {
    if (files.length === 0) {
      return;
    }


    const formData = new FormData();
    formData.append('deleteOldFiles', deleteOldFiles ? 'true' : 'false');

    files.forEach((file, index) => {
      formData.append('files', file);
    });

    
    try {
      const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        console.log("File uploaded successfully!");
       
        onFilesUploaded(files);
      } else {
        console.log("Failed to upload file.");
      }
    } catch (error) {
      console.log("Error occurred while uploading the file:", error);
    }
  }
  
  return (
      
      <Box 
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        border="2px dashed"
        borderColor="daoPurple"
        borderRadius="md"
        bgColor="white"
        p="6"
        textAlign="center"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current.click()}
        {...props}
      >
        
        <Image mb="4" src="/file.png" alt="File" />
        
        {uploading ? (
        <>
          <Heading as="h3" mb={2} color="daoPurple">
            Uploading...
          </Heading>
        
          
        </>
      ) : (
        <Heading as="h3" mb={2} color="daoPurple">
          Drag and drop files here
        </Heading>
      )}
      {!uploading && (
        <Text fontSize="sm" color="gray.500" mb={4}>
          or click to select files
        </Text>
      )}
      <Progress value={progress} size="md" w="100%" mb={8} mt={8}/>

        <input type="file" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileInputChange} multiple />
      </Box>
      
  );
}

export default FileUploader;