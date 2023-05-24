import { Box, Flex, Heading, IconButton } from '@chakra-ui/react';
import { MdRemoveCircle } from 'react-icons/md';

function FilesList({ fileList, removeFile, ...props }) {
  const onRemove = (e) => {
    removeFile(e.currentTarget.getAttribute('data-index'));
  }

  return (
    <Flex direction="column">
      <Heading as="h4" size="md" mt="4" mb="4" color="daoPurple" textAlign="center">Your Uploaded Files</Heading>
      {fileList.map((item, idx) => (
        <Box key={idx} color="gray.600" display="flex" direction="row" fontSize="1vw" p="5">
          <Box flex="1">{item.name} <small>X pages</small></Box>
          <Box>
            <IconButton icon={<MdRemoveCircle/>} data-index={idx} bgColor="lightpink" onClick={onRemove}/>
          </Box>
        </Box>
      ))}
    </Flex>
    
  );
}

export default FilesList;