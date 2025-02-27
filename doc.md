# API Documentation

### POST /api/v1

#### Description

Cette route permet d'obtenir les informations d'une quittance à partir d'un fichier PDF ou image. Le fichier doit être envoyé en tant que champ `file` dans un formulaire `multipart/form-data`.

#### Request

- **Method**: POST
- **Content-Type**: `multipart/form-data`
- **Field**:
  - `file`: Fichier PDF ou image à télécharger.

#### Headers

| Key          | Value               |
| ------------ | ------------------- |
| Content-Type | multipart/form-data |

#### Body

Le corps de la requête doit contenir le fichier dans le champ `file`.

Exemple :

```js
import axios from "axios";

const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  try {
    let config = {
      method: "post",
      maxBodyLength: Infinity,
      Headers: {
        "Content-Type": "multipart/form-data",
      },
    };

    let data = {};

    await axios
      .post("http://localhost:8000/api/v1/", formData, config)
      .then((response) => {
        data = response.data.data;
      })
      .catch((error) => {
        console.log(error);
      });

    return data;
  } catch (error) {
    console.error("Erreur:", error);
    // throw error;
  }
};

export default uploadFile;
```

#### Responses

- **200 OK**: Si le fichier a été téléchargé et traité avec succès.
  - **Content-Type**: `application/json`
  - **Body**:
    ```json
    {
      "data": {
        "amount": "12345",
        "student_name": "John Doe",
        "stamp_fees": "100",
        "currency": "USD",
        "date": "2023-07-01",
        "reference": "INV123456",
        "payment_reason": "Tuition Fee"
      }
    }
    ```
- **400 Bad Request**: Si le fichier n'est pas fourni ou si le format est incorrect.
  - **Content-Type**: `application/json`
  - **Body**:
    ```json
    {
      "error": "Unsupported file type. Only PDF and images are allowed."
    }
    ```
- **500 Internal Server Error**: Si la réponse du modèle ne peut pas être analysée.
  - **Content-Type**: `application/json`
  - **Body**:
    ```json
    {
      "error": "Failed to parse response from model"
    }
    ```

#### Example Curl Request

```sh
curl -X POST http://your-domain.com/api/v1 \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/file.pdf"
```
