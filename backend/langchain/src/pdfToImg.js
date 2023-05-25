import { exportImages } from 'pdf-export-images';

export const extractImgsFromPdf = (file) => {
    return new Promise(() => {
        exportImages('src/healthDAODocs/unstructure/files/'+file, 'src/healthDAODocs/unstructure/images/')
        .then(images => console.log('Exported', images.length, 'images'))
        .catch(console.error)
    })
}