import { Box, Input, IconButton,Text} from "@chakra-ui/react";
import { useState } from "react";
import { FaPaperPlane } from "react-icons/fa";

const sendMessageUrl = process.env.REACT_APP_SEND_MESSAGE_ENDPOINT;

// Define your arguments or replace with a more robust solution like yargs or command-line-args
const args = {
  controllerAddress: 'http://0.0.0.0:21001',
  workerAddress: 'http://127.0.0.1:21002',
  modelName: 'meditron-7b', // Replace with actual model name
  temperature: 0.3,
  maxNewTokens: 512,
};

function Chat({userId,...props}) {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [inputValue, setInputValue] = useState("");
  const [loadingResp, setLoadingResp] = useState(false);

  async function handleSendMessage() {
    if (inputValue.trim() !== "" ) {
      setInputValue("");
      setLoadingResp(true);

      setMessages([...messages, { "class":"user-msg", "msg": inputValue}]);
      
      const prompt = `You are a helpful, respectful and honest assistant.Always answer as helpfully as possible, while being safe.Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content.Please ensure that your responses are socially unbiased and positive in nature.
      If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct.If you don't know the answer to a question, please don't share false information.
      ### Human: What happens if listeria is left untreated?
      ### Assistant: If listeria infection, or listeriosis, is left untreated, it can lead to severe health complications, particularly in certain high-risk groups. Here's a general overview of the potential outcomes:
      1. Spread of the Infection: Untreated listeriosis can spread beyond the gut to other parts of the body, including the nervous system. This can lead to more severe conditions like meningitis (inflammation of the membranes surrounding the brain and spinal cord) and septicemia (a serious blood infection).
      2. Increased Risk for Certain Groups: Pregnant women, newborns, the elderly, and individuals with weakened immune systems are at a higher risk of severe complications. In pregnant women, listeriosis can lead to miscarriage, stillbirth, premature delivery, or life-threatening infection of the newborn.
      3. Neurological Effects: Listeriosis can cause severe neurological symptoms like headaches, stiff neck, confusion, loss of balance, and convulsions, especially when the infection spreads to the nervous system.
      4. Long-Term Health Impacts: For some, particularly those with pre-existing health conditions or weakened immune systems, the health impacts of listeriosis can be long-lasting and may not fully resolve even with treatment.
      5. Fatalities: In severe cases, particularly among high-risk groups, listeriosis can be fatal.
      It's important to note that early diagnosis and appropriate treatment, typically with antibiotics, can greatly improve the prognosis for those with listeriosis. Therefore, seeking medical attention promptly if listeriosis is suspected is crucial.
      ### Human: ${inputValue}
      ### Assistant:`
      
      const genParams = {
        model: args.modelName,
        prompt: prompt,
        temperature: args.temperature,
        max_new_tokens: args.maxNewTokens,
        stop: "###",
        echo: false,
      };
      
      const response = await fetch('http://127.0.0.1:21002/worker_generate_stream', {
        method: 'POST',
        headers: { 'User-Agent': 'FastChat Client'},
        body: JSON.stringify(genParams),
        stream: true,
      });

      

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let result = '';
      setLoadingResp(false);
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }
    

        if (value) {
          const text = decoder.decode(value).slice(0, -1);
          const data = JSON.parse(text);
          result = data.text;
   
          setMessages((prevMessages) => {
            const lastMessage = prevMessages[prevMessages.length - 1];
          
            if (lastMessage && lastMessage.class === "system-msg") {
              return [...prevMessages.slice(0, -1), { class: "system-msg", msg: result }];
            } else {
              return [...prevMessages, { class: "system-msg", msg: result }];
            }
          });

        }
      }


      
      //setHistory([...history, { "input": inputValue}]);
      //setInputValue("");
      //setLoadingResp(true);
      //try {
      //  const response = await fetch(sendMessageUrl, {
      //    method: "POST",
      //    mode: "cors",
      //    credentials: 'include',
      //    headers: {
      //      "Content-Type": "application/json"
      //    },
      //    body: JSON.stringify({ message: inputValue, history: history, userId:userId})
      //  });

      //  setLoadingResp(false);

        //const reader = response.body.getReader();
        //const decoder = new TextDecoder();
        //let result = '';
        //while (true) {
        //  const { done, value } = await reader.read();
        //  if (done) {
        //    break;
        //  }
          

        //  if (value) {
        //    const text = decoder.decode(value);
        //    result += text;
   
        //    setMessages((prevMessages) => {
        //      const lastMessage = prevMessages[prevMessages.length - 1];
        //    
        //      if (lastMessage && lastMessage.class === "system-msg") {
        //        return [...prevMessages.slice(0, -1), { class: "system-msg", msg: result }];
        //      } else {
        //        return [...prevMessages, { class: "system-msg", msg: result }];
        //      }
        //    });

        //  }
        //}
        
        //setHistory(history => [...history, { "output": result }]);
      //} catch (error) {
      //  setLoadingResp(false);
      //  console.error(error);
        // Manejar el error en la solicitud
      //}

      
      
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
            <Text whiteSpace="pre-wrap">{message.msg}</Text>
            
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
          isDisabled={loadingResp}
          {...props}
        />
        <IconButton aria-label='Send' icon={<FaPaperPlane />} bgColor="daoPurple" onClick={handleSendMessage} isDisabled={loadingResp}/>
      </Box>
    </Box>
  );
}

export default Chat;