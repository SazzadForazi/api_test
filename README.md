# Mock Practice API Sandbox for Testers

A comprehensive mock API sandbox built with **FastAPI** to practice API testing (REST, validation checks, authentication tokens, cookie sessions, multipart file uploads, rate limiting, and edge-case simulation).

---

## 🚀 Quick Start Guide

### Option A: Using the Startup Script (Recommended)
1. Navigate to the project folder:
   ```bash
   cd /home/tigerit/Desktop/test_api
   ```
2. Run the startup script:
   ```bash
   ./run.sh
   ```
   *This automatically sets up a Python virtual environment, installs dependencies, and boots the FastAPI server on port 8000.*

### Option B: Running Manually from Terminal
If you prefer to run it manually without the shell script:
```bash
# 1. Activate the environment
source venv/bin/activate

# 2. Run the Uvicorn server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🌐 Server Pages

### Live Production Deployment
* **Live Sandbox Dashboard**: [https://api-test-nine-omega.vercel.app/](https://api-test-nine-omega.vercel.app/)
* **Live Swagger UI Documentation**: [https://api-test-git-main-team-forazi.vercel.app/docs](https://api-test-git-main-team-forazi.vercel.app/docs)
* **Live ReDoc Documentation**: [https://api-test-git-main-team-forazi.vercel.app/redoc](https://api-test-git-main-team-forazi.vercel.app/redoc)

### Local Development
Once the server is running locally, access these URLs:
* **Local Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Local Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Local ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)


---

## 👥 Authentication & Roles
Use these credentials for testing authentication endpoints:

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `password123` | `admin` | Full access (Read, Create, Update, Delete Products) |
| `tester` | `testpass` | `tester` | Read, Create, and Update Products |
| `user` | `userpass` | `user` | Read-only access |

---

## 📬 Postman Testing Guide

### 1. Authentication Endpoints

#### Login & Set Session
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/auth/login`
* **Body** (`raw` -> select `JSON`):
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```
* *Tip: Postman automatically saves the HTTP-only cookie called `access_token` in its cookie jar.*

#### Get Active User Profile
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/auth/me`
* **Option A**: Go to **Authorization** -> select **Bearer Token** -> paste the `access_token` from the login response.
* **Option B**: Send the request with **No Auth** (Postman will automatically pass the saved login cookie).

#### Logout & Clear Session
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/auth/logout`

---

### 2. Products CRUD (In-Memory Data)

#### List Products (Filters & Pagination)
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/products`
* **Query Parameters (Params)**:
  - `category` (e.g. `Electronics` or `Footwear`)
  - `in_stock` (`true` or `false`)
  - `min_price` (`20.0`)
  - `max_price` (`80.0`)
  - `q` (e.g. `Keyboard` - search title/description)
  - `skip` (`0`), `limit` (`10`)

#### Get Single Product
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/products/1`

#### Create Product (Requires `tester` or `admin` token)
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/products`
* **Headers**: `Authorization: Bearer <your_access_token>`
* **Body** (`raw` -> `JSON`):
  ```json
  {
    "name": "Noise Cancelling Headphones",
    "price": 149.99,
    "category": "Electronics",
    "in_stock": true,
    "description": "Premium wireless headphones with ANC."
  }
  ```

#### Update Product (Requires `tester` or `admin` token)
* **Method**: `PUT`
* **URL**: `http://127.0.0.1:8000/api/v1/products/1`
* **Headers**: `Authorization: Bearer <your_access_token>`
* **Body** (`raw` -> `JSON`):
  ```json
  {
    "price": 19.99,
    "in_stock": false
  }
  ```

#### Delete Product (Requires `admin` token)
* **Method**: `DELETE`
* **URL**: `http://127.0.0.1:8000/api/v1/products/1`
* **Headers**: `Authorization: Bearer <your_access_token>`

#### Reset Database to Defaults
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/products/reset`

---

### 3. File Uploads

#### Upload Image
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/upload/image`
* **Body** (select **form-data**):
  - Key: `file` (hover over key, click dropdown next to it, and change it from `Text` to `File`)
  - Value: Choose a local image file (PNG/JPEG under 5MB)

#### Upload Text File
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/upload/text`
* **Body** (select **form-data**):
  - Key: `file` (change type to `File`)
  - Value: Select a plain text file (`.txt`)

---

### 4. Codecs & Utilities

#### Base64 Encode
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/codec/base64/encode`
* **Body** (`raw` -> `JSON`):
  ```json
  {
    "text": "Hello World"
  }
  ```

#### Base64 Decode
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/codec/base64/decode`
* **Body** (`raw` -> `JSON`):
  ```json
  {
    "code": "SGVsbG8gV29ybGQ="
  }
  ```

#### Decode JWT Token Payload
* **Method**: `POST`
* **URL**: `http://127.0.0.1:8000/api/v1/codec/jwt/decode`
* **Body** (`raw` -> `JSON`):
  ```json
  {
    "token": "<paste_jwt_token_here>"
  }
  ```

---

### 5. Simulators & Edge-Cases

#### Network Timeout/Delay Simulator
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/simulate/delay/3` *(delays response by 3 seconds. Range: 1-10s)*

#### HTTP Status Code Simulator
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/simulate/status/418` *(forces a teapot status or 500 internal error)*

#### Echo Headers
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/simulate/headers`
* *Tip: Add custom headers in Postman's **Headers** tab to see them in the return body.*

#### Rate Limit Simulator
* **Method**: `GET`
* **URL**: `http://127.0.0.1:8000/api/v1/simulate/rate-limit`
* *Tip: Click send 6 times fast to see it trigger `429 Too Many Requests` status.*

---

## 🧪 Automated Testing
Run integration tests to verify code stability:
```bash
./run.sh test
```

---

## ☁️ Deploying to Vercel
Deploy to the cloud using the Vercel CLI:
1. Install globally:
   ```bash
   npm install -g vercel
   ```
2. In the project root, run:
   ```bash
   vercel
   ```
3. Follow the prompt instructions. The application will build serverless functions automatically using configuration rules in `vercel.json` and entrypoint `api/index.py`.
