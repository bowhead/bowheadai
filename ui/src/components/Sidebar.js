import { Box, Flex, Heading } from '@chakra-ui/react';

function Sidebar({ fileList, removeFile, ...props }) {
  


  return (
    <Flex direction="column">
      <Heading as="h4" size="md" mt="4" mb="4" color="daoPurple" textAlign="center">Your Uploaded Files</Heading>
      {fileList
        .filter((item, index, self) => self.findIndex((el) => el.name === item.name) === index) // Filter out duplicates
        .map((item, idx) => (
          <Box key={idx} color="gray.600" display="flex" direction="row" fontSize="1vw" p="5">
            <Box flex="1">{item.name} <small>X pages</small></Box>
            
          </Box>
        ))}
    </Flex>
  );
  
}

export default Sidebar;
