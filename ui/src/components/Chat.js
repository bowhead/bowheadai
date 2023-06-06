import { Box, Input, IconButton} from "@chakra-ui/react";
import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

function Chat({userId,...props}) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loadingResp, setLoadingResp] = useState(false);

  async function handleSendMessage() {
    if (inputValue.trim() !== "" ) {
      setMessages([...messages, { "class":"user-msg", "msg": inputValue}]);
      setInputValue("");
      setLoadingResp(true);
      try {
        const response = await fetch("http://localhost:3001/send-message", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ message: inputValue, history: messages, userId:userId})
        });

        setLoadingResp(false);

        if (response.ok) {
          const responseData = await response.json();
          setMessages(messages => [...messages, { "class": "system-msg", "msg": responseData.response }]);
        } else {
          throw new Error("Error en la solicitud");
        }
      } catch (error) {
        console.error(error);
        // Manejar el error en la solicitud
      }

      
      
    }
  }

  function handleInputValueChange(event) {
    setInputValue(event.target.value);
    
  }

  function handleKeyPress(event) {
    if (event.key === "Enter") {
      handleSendMessage();
    }
  }
  

  return (
    <Box p={4}>
      <Box height="80vh" width="83%" sx={{ overflow: "auto" }} flex="1">
        {messages.map((message, index) => (
          <Box
            key={index}
            p={2}
            color="black"
            borderRadius="md"
            mb={2}
            className={message.class}
          >
            {message.msg}
          </Box>
        ))}
        {loadingResp && <Box alignItems="center">
          <img src={process.env.PUBLIC_URL + 'loader.gif'} alt="loader"/>
        </Box>}
        
      </Box>

      <Box>
        <Input 
          value={inputValue}
          color="black"
          onChange={handleInputValueChange}
          onKeyPress={handleKeyPress}
          placeholder="Message..."
          {...props}
        />
        <IconButton aria-label='Send' icon={<FaPaperPlane />} bgColor="daoPurple" onClick={handleSendMessage}/>
      </Box>
    </Box>
  );
}

export default Chat;