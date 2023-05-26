import { Box, Heading, Text } from "@chakra-ui/react";
import { useState, useRef, useEffect } from "react";

function FileUploader({ onFilesUploaded,deleteOldFiles,  ...props }) {
  const fileInputRef = useRef(null);
  const [files, setFiles] = useState([]);
  
  useEffect(() => {
    if (files.length > 0) {
      createVector();
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
        border="2px dashed"
        borderColor="daoTeal"
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
        <Heading as="h3" mb="4" color="daoPurple">Drag and drop files here</Heading>
        <Text fontSize="sm" color="gray.500">
          or click to select files
        </Text>
        <input type="file" style={{ display: "none" }} ref={fileInputRef} onChange={handleFileInputChange} multiple />
      </Box>
      
  );
}

export default FileUploader;