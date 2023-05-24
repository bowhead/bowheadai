import { Box, IconButton, Input } from '@chakra-ui/react';
import { FaPaperPlane } from 'react-icons/fa';

function Search({...props}) {


  return (
    <Box>
      <Input placeholder="Chat with your health data" {...props}/>
      <IconButton aria-label='Send' icon={<FaPaperPlane />} bgColor="daoPurple"/>
    </Box>
  );
}

export default Search;