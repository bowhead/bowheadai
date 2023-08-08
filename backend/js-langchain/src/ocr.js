import Tesseract from 'tesseract.js';
import fs from 'fs';

export const extractText = (image) => {
    return new Promise((resolve,reject) => {
        Tesseract.recognize(
        'src/healthDAODocs/unstructure/images/'+image,
        'eng'
        ).then(({ data: { text } }) => {
            console.log("Extracting: "+image.split('.')[0])
            fs.writeFile('src/healthDAODocs/unstructure/text/' + image.split('.')[0] + '.txt', text, err => {
                if (err) {
                  console.error(err);
                }
                // file written successfully
              });
        })
    })

}