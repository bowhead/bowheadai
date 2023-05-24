import { Box, Heading, Text } from '@chakra-ui/react';

function FileUploader({ filesAddedCallback, ...props}) {
  const fileSelector = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.onchange = () => {
      uploadFiles(input.files);
    };
    input.click();
  }

  const handleFileUpload = (event) => {
    event.preventDefault();
    uploadFiles(event.dataTransfer.files);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const uploadFiles = (fileList) => {
    filesAddedCallback(fileList);
  }

  return (
    <Box
      border="2px dashed"
      borderColor="daoTeal"
      borderRadius="md"
      bgColor="white"
      p="6"
      textAlign="center"
      onDrop={handleFileUpload}
      onDragOver={handleDragOver}
      onClick={fileSelector}
      {...props}
    >
      <Heading as="h3" mb="4" color="daoPurple">Drag and drop files here</Heading>
      <Text fontSize="sm" color="gray.500">
        or click to select files
      </Text>
    </Box>
  );
}

export default FileUploader;